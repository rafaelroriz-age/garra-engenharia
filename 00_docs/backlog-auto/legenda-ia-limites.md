# T35 — Limite de taxa, teto e saneamento da legenda por IA (DEC-42 C e D)

- **Tarefa:** T35. Sem adapter real e sem provedor escolhido (B-04). DEC-42 continua **proposta** até o dono aprovar.
- **Branch:** `worktree-backlog-T35` (sem push). Commit: `feat(backend): limites e saneamento da legenda por IA (DEC-42)`, `Refs DEC-42`.
- **Sem** migration, sem mudança em models/schemas, sem frontend, sem editar `fotos.py` nem os documentos de gestão.

## 1. Resultado em uma tabela

| Critério de pronto | Situação | Evidência |
|---|---|---|
| Limite por usuário e por foto, excedido → 429 RFC 7807 | Feito e verificado na rota real | `tests/test_legenda_ia_limites.py`, 53 passed |
| Saída saneada e com teto (`legenda_ia_sugerida`, alertas, pendências) | Feito e verificado na rota real | idem |
| `legenda_bruta` delimitada ao chegar no cliente | Feito e verificado na rota real | idem |
| Variáveis nos dois `.env.example` | Feito, **mas** no Docker só valem depois de mudar o compose | §6, pendência 2 |
| `test_legenda_ia_endpoints.py` e `test_prompt_ia_service.py` | **Não rodaram** (PostgreSQL fora do ar) | §7 |
| Header `Retry-After` no 429 | **Não entregue** (`Retry-After` vai no corpo) | §6, pendência 1 |

## 2. Divergências encontradas no enunciado

| Enunciado | Realidade | Efeito |
|---|---|---|
| Worktree com T23/T25 prontas | Nasceu de `origin/main` (`14ead2f`), 170 commits atrás da `main` local (`d693ca5`), sem `app/services/legenda_ia/` nem os docs citados | `git merge --ff-only main` na branch do worktree, antes de qualquer commit. Só esta branch andou; `main` não foi tocada. É a mesma correção de T25 e T29. **`worktree-backlog-T34` está na mesma base antiga** |
| SEG-IA-01, SEG-IA-02, SEG-IA-06 | Em `seguranca-legenda-ia.md`, os itens de DEC-42 C/D são **SEG-IA-01, SEG-IA-04 e SEG-IA-08**. SEG-IA-02 é regerar aprovada (T33) e SEG-IA-06 é auxiliar remover foto aprovada | Implementado o que o texto da tarefa e DEC-42 descrevem. **SEG-IA-06 continua aberto** e não está em nenhum item de DEC-42 |
| `get_legenda_ia_client` em `deps.py` | Está em `app/services/legenda_ia/__init__.py` | Ver §3 |

## 3. Como ficou ligado (sem editar `fotos.py`)

A rota já declara `Depends(get_legenda_ia_client)`, então a proteção entrou nessa dependência. **Nenhuma linha precisa ser adicionada ao endpoint.**

```text
fotos.py: Depends(get_legenda_ia_client)
  ├─ obter_cliente_provedor        503 enquanto B-04 estiver aberto; o adapter real entra AQUI
  ├─ deps.limitar_geracao_legenda_ia   429 antes de baixar a imagem
  └─ ClienteLegendaIAProtegido     delimita a entrada, chama o provedor, saneia a saída
```

| Arquivo | Conteúdo |
|---|---|
| `app/services/legenda_ia/__init__.py` | `get_legenda_ia_client`, `obter_cliente_provedor`; reexporta os nomes de antes |
| `app/services/legenda_ia/contrato.py` | `LegendaIAClient`, `LegendaIAResultado`, `FakeLegendaIAClient` (movidos sem mudança) |
| `app/services/legenda_ia/limites.py` | `LimitadorLegendaIA` (relógio injetável), `RegraLimite`, `LimiteLegendaIAExcedido` |
| `app/services/legenda_ia/saneamento.py` | `sanear_resultado`, `delimitar_legenda_bruta`, `ClienteLegendaIAProtegido` |
| `app/api/deps.py` | `limitar_geracao_legenda_ia`, `get_limitador_legenda_ia` |
| `app/core/config.py` | 8 variáveis novas, validadas no boot |

**Custo desse desenho:** para não tocar `fotos.py`, `app/services/legenda_ia` importa `app.api.deps`, uma inversão de camada, e `deps.py` tem um import tardio para evitar ciclo. Testei as duas ordens de import (§7). Proposta: quando `fotos.py` puder ser editado, o endpoint declara a dependência protegida e essa inversão some.

`app/core/rate_limit.py` (DEC-24) não pôde ser reaproveitado direto: conta falhas de login, com constantes fixas e relógio embutido. `limites.py` usa o mesmo mecanismo (janela deslizante em memória, com `Lock`).

## 4. Parâmetros

| Variável | Default | Validação | Efeito |
|---|---|---|---|
| `LEGENDA_IA_LIMITE_POR_USUARIO` | 10 | ≥ 1 | Tentativas por usuário na janela curta |
| `LEGENDA_IA_JANELA_USUARIO_SEGUNDOS` | 60 | ≥ 1 | Janela curta |
| `LEGENDA_IA_LIMITE_DIARIO_POR_USUARIO` | 200 | ≥ 1 | Teto por usuário em 86400 s |
| `LEGENDA_IA_LIMITE_POR_FOTO` | 5 | ≥ 1 | Tentativas por foto, somando todos os usuários |
| `LEGENDA_IA_JANELA_FOTO_SEGUNDOS` | 3600 | ≥ 1 | Janela da foto |
| `LEGENDA_IA_SAIDA_MAX_CARACTERES` | 500 | 1 a 500 | Teto de `legenda_ia_sugerida` |
| `LEGENDA_IA_SAIDA_MAX_ITENS` | 20 | ≥ 1 | Teto de `alertas` e de `pendencias`, cada um |
| `LEGENDA_IA_SAIDA_MAX_CARACTERES_ITEM` | 300 | ≥ 1 | Teto de cada alerta ou pendência |

Valor inválido impede o boot. Os defaults são escolha minha, sem medição de uso real: 200/dia pode ser pouco para um relatório grande, e o dono deve revê-los. O teto de 500 acompanha `LEGENDA_MAX_LENGTH`, porque aprovar copia a sugestão para `legenda` sem passar pelo limite do payload.

## 5. Escolhas

| Tema | Escolha | Motivo |
|---|---|---|
| Saída acima do teto | **Trunca** (em palavra, com `…`) e acrescenta aviso em `pendencias` | O texto é rascunho e passa por aprovação humana (RN-16); rejeitar perderia uma chamada paga e gastaria cota com nova tentativa. SEG-IA-04 sugeria 502; preferi manter o rascunho e deixar o corte visível |
| Saída sem texto após saneamento | **502** `legenda-ia-saida-invalida`, nada gravado | Não há o que revisar |
| O que conta na cota | **A tentativa**, antes de baixar a imagem | Atômico sob concorrência e barra o download. Efeito: foto inexistente (404) e erro do provedor gastam cota. 401, 403, 503 sem provedor e recusas 429 não gastam |
| Recusa por uma regra | Não gasta cota das outras | Martelar uma foto bloqueada não consome a cota do usuário |
| Marcação | Remove `script`/`style` com conteúdo, tags, `javascript:`, `vbscript:`, `data:<mime>`; decodifica entidades e repete até estabilizar | `&lt;script&gt;` e `<scr<script>ipt>` também caem |
| Texto técnico | Preserva `< 0,5 mm`, `> 0,2 mm`, `m²`, `Data: 12/03/2026` | Só é tag se `<` vier seguido de letra, `/`, `!` ou `?`. **Limitação:** `a<b e c>d` é tratado como tag e perde esse trecho; o revisor vê o rascunho |
| Controle | Remove categorias Unicode Cc, Cf, Cs, Co, Cn; junta espaços e quebras | NUL quebra o `text` do Postgres; largura zero e bidi escondem texto |
| Injeção de prompt | Delimita, não filtra: `<<<LEGENDA_BRUTA_INICIO>>>` / `<<<LEGENDA_BRUTA_FIM>>>`, com aviso fixo antes. Sequências `<<<` e `>>>` do usuário caem para duas | Não existe filtro confiável de «ignore as instruções». O texto não consegue fechar o bloco. **Isto reduz o risco, não o elimina** |
| Prompt versionado | Não é alterado | `prompt_conteudo_hash` precisa continuar sendo o hash do que foi enviado (DP-2) |
| O que é gravado | `fotos.legenda_bruta` guarda o texto **original** | Delimitadores existem só no envio (RN-17) |

## 6. Limitações e pendências

| # | Pendência | Bloqueia produção? | Ação |
|---|---|---|---|
| 1 | **Sem header `Retry-After`.** `_handle_domain_error` não repassa headers, e `errors.py`/`exception_handlers.py` estão fora de `Toca`. O valor vai em `errors[].field = "retry_after_segundos"` e no `detail` | Não | Dar `headers` a `DomainError` e repassar em `_problem_response`; o atributo `retry_after` já existe na exceção |
| 2 | **Variáveis não chegam ao container.** `docker-compose.yml` e `docker-compose.prod.yml` listam o `environment:` do backend uma a uma, e `render.yaml` idem; todos fora de `Toca`. Hoje, em Docker e no Render, valem só os defaults | Não (defaults valem), mas ajustar um limite não terá efeito | Acrescentar `LEGENDA_IA_LIMITE_POR_USUARIO: ${LEGENDA_IA_LIMITE_POR_USUARIO:-10}` e equivalentes |
| 3 | **Janela em memória por processo.** Com N workers/réplicas o limite efetivo vira N vezes o configurado, e reiniciar zera a contagem | Sim, se houver mais de um worker | Migrar para Redis (ADR-06/DEC-10) ou banco, mantendo `consumir` |
| 4 | **Sobrescrever `get_legenda_ia_client` desliga as proteções.** É o que `test_legenda_ia_endpoints.py` e `test_seguranca_legenda_ia.py` fazem | Não (só testes); o adapter real tem de entrar em `obter_cliente_provedor` | Ver pendência 5 |
| 5 | **Marcas `xfail` desatualizadas** em `test_seguranca_legenda_ia.py` (fora de `Toca`). `test_gerar_tem_limite_de_taxa_por_usuario` e `test_sugestao_longa_do_llm_nao_burla_limite_da_legenda` sobrescrevem `get_legenda_ia_client`, então seguirão em xfail mesmo com a correção | Não | Trocar a sobrescrita por `obter_cliente_provedor` e remover as marcas. Sem isso, esses dois testes não provam nada |
| 6 | Caminho completo com banco real + wrapper não foi exercitado: `test_legenda_ia_limites.py` usa banco em memória, e os testes com banco usam a sobrescrita | Não | Coberto pela pendência 5 |
| 7 | Sem orçamento global: 200/dia é por usuário, então o custo total cresce com o número de usuários | Sim, antes do adapter pago | SEG-IA-01 prevê orçamento diário no adapter (BL-34) |

**Continua bloqueando produção do adapter real:** B-04 (provedor não escolhido); R-10 (retenção e privacidade da imagem enviada ao provedor); L15/SEG-IA-07 (sem vínculo usuário↔contrato, qualquer pessoa da equipe gera legenda em foto de qualquer contrato, o que soma custo a acesso cruzado); revisão do adapter por SEG-IA-08 (prompt como mensagem de sistema, `legenda_bruta` em mensagem separada, saída estruturada, sem ferramentas nem URLs).

**Para o fechamento de lote (não editei):** registrar em `decisoes.md` o andamento de DEC-42 C e D; em `seguranca-legenda-ia.md`, SEG-IA-01/04 corrigidos e SEG-IA-08 mitigado do lado do contrato; em `riscos.md`, as pendências 3 e 7; decidir o destino de SEG-IA-06.

## 7. Comandos e saídas

Ambiente: `127.0.0.1:5433` e `127.0.0.1:9000` **fechadas** (`TcpClient`) e `docker` inexistente nesta máquina, logo `docker compose ps` não pôde rodar. Nenhum serviço foi subido nem derrubado. Python 3.12.4 do `.venv` do checkout principal; ruff 0.15.1. Comandos a partir de `04_backend`. Variáveis `POSTGRES_HOST=127.0.0.1`, `POSTGRES_PORT=5433`, `MINIO_HOST=127.0.0.1` só no processo; nenhum `.env` foi copiado.

| Comando | Saída |
|---|---|
| `pytest tests/test_legenda_ia_limites.py` (antes de implementar) | `1 error during collection`: módulos inexistentes |
| `pytest tests/test_legenda_ia_limites.py` | **53 passed**, 1 warning in 5.99s |
| `pytest tests/test_legenda_ia_limites.py tests/test_legenda_ia_endpoints.py tests/test_prompt_ia_service.py` | **5 failed, 57 passed, 21 errors** in 64.03s. Dos 57, 53 são de limites; os outros 4 não dependem do banco para o que afirmam. **As falhas e os erros são todos conexão recusada, não regressão** |
| `pytest tests/test_legenda_ia_endpoints.py tests/test_prompt_ia_service.py tests/test_seguranca_legenda_ia.py tests/test_legenda_relatorio.py -rA` | 5 failed, 12 passed, 6 xfailed, 32 errors; único tipo de erro nomeado: `ConnectionRefusedError` (37 ocorrências). **Os 6 xfailed não valem como evidência:** falharam por conexão, e o `xfail` esconde a causa |
| `pytest --collect-only` | 406 coletados, 5 erros de coleta em `test_{ltip,rfip,rfo,vistoria_cautelar,vistoria_residencial}_templates.py`. Causa: `ModuleNotFoundError` de `pdfplumber` e `openpyxl` nesse `.venv`, sem relação com esta tarefa |
| Importar em ordens diferentes (`app.api.deps` antes e depois de `app.services.legenda_ia`; `limites`, `foto_service`, `app.api.v1.fotos`, `app.main`) | as 6 ordens com código de saída 0 |
| `get_limitador_legenda_ia` real, com defaults, sem sobrescrita | instância única; `5 aceitas na mesma foto, depois 429 retry_after=3600` |
| `ruff check .` | `Found 11 errors`, nenhum nos arquivos tocados (`vistoria_cautelar_layout_extractor.py`, `test_foto_origem_enum.py`, `test_ocorrencias_regras.py`, `test_storage_legenda_ia.py`, `test_vistoria_cautelar_{pipeline,templates}.py`) |
| `ruff check app/services/legenda_ia app/api/deps.py app/core/config.py tests/test_legenda_ia_limites.py` | `All checks passed!` |
| `pytest` completo | **Não rodou**: precisa de PostgreSQL e MinIO |
| `npm run lint` / `npm run build` | Não se aplica (frontend não tocado) |

**Para concluir a verificação**, com PostgreSQL e MinIO no ar:

```bash
cd 04_backend
pytest tests/test_legenda_ia_limites.py tests/test_legenda_ia_endpoints.py tests/test_prompt_ia_service.py tests/test_seguranca_legenda_ia.py
```

Atenção ao resultado de `test_seguranca_legenda_ia.py`: as correções de T33 devem fazer `test_regerar_apos_aprovar_limpa_aprovacao_anterior`, `test_editar_legenda_aprovada_nao_atribui_edicao_ao_aprovador_anterior` e `test_auxiliar_nao_aprova_legenda_ia` passarem, e o `strict` transforma isso em falha até as marcas `xfail` saírem. Não é regressão desta tarefa, e não pude confirmar sem o banco.

Rodar `test_legenda_ia_endpoints.py` junto com `test_prompt_ia_service.py` já quebrava estes últimos em T25 (`There is no current event loop`). Os testes novos não usam `asyncio.run`, para não agravar isso.
