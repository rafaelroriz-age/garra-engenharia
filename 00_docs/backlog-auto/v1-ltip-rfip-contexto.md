# V1-03 · Emissão do LTIP e do RFIP a partir do banco (T59)

Papel: Engenheiro Backend. Data: 2026-11-11. Branch: `worktree-backlog-T59`.

> **Nota de ambiente:** o worktree nasceu de uma base antiga (`14ead2f`, sem a V1-01/V1-02). Como a branch não tinha commits próprios, fiz `git merge --ff-only main` antes de começar. Nada foi reescrito.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `04_backend/app/services/report_generator/contexto_comum.py` (novo) | `carregar_inspecao(db, id, TipoServico)` (404; 409 `inspecao-nao-{tipo}`), `inspecao_ctx`, `fiscal_ctx`, `edificacao_ctx`, `contrato_ctx`, `foto_ctx` (legenda só por `legenda_para_relatorio`, vazia vira '—'), `ocorrencia_ctx` (sistema/subsistema com `sistema_ordem`/`subsistema_ordem`, GUT, grau de risco, prioridade, localização), `ocorrencias_ctx`, `primeiras_fotos`, `texto_ou_traco`, `data_br`, `fotos_ordenadas`, `vazio` e `validar_obrigatorios`. |
| `.../ltip_contexto.py` (novo) | `TIPO_LTIP`, `montar_contexto_ltip`, `validar_contexto_ltip`, `extrair_fotos_ltip`. |
| `.../rfip_contexto.py` (novo) | `TIPO_RFIP`, `montar_contexto_rfip`, `validar_contexto_rfip`, `extrair_fotos_rfip`. |
| `.../rfo_contexto.py` | Usa `data_br`, `texto_ou_traco` e `fotos_ordenadas` do comum (só o trivial). A saída do RFO não mudou; `_data_br` e `_texto_ou_traco` continuam importáveis daí (`tests/test_rfo_art_execucao.py`). |
| `app/services/relatorio_service.py` | Registra `LTIP` (`ltip_pipeline`) e `RFIP` (`rfip_pipeline`) em `EMISSORES`. Nenhuma rota nova: `POST /inspecoes/{id}/relatorios/{LTIP\|RFIP}` já serve. |
| `tests/test_ltip_rfip_contexto.py` (novo) | 16 casos (4 de unidade, 12 com banco). |
| `tests/test_relatorios_emissao_generica.py` | `test_registrar_emissor_com_tipo_divergente_falha` usava `"LTIP"` como tipo não registrado; agora usa `"INEXISTENTE"`. |

## Contexto montado

**LTIP** (`ltip_pipeline.normalizar_contexto`): `inspecao`, `edificacao` (nome, endereço, cep, tipologia, sistema construtivo, pavimentos, área), `fiscal` (nome, título, CREA, e-mail, telefone), `contrato` (número, tipo, objeto, `art_fiscalizacao`), `data_emissao` (do conteúdo, senão hoje; **já em `dd/mm/aaaa`**, porque `ltip_pipeline._formatar_data` devolve uma string ISO sem converter), `local_emissao` (se salvo), `ocorrencias` planas e os sete textos como `<chave>_paragrafos` (lista).

- Os textos saem como `<chave>_paragrafos`, e não como `<chave>`: `ltip_pipeline._em_paragrafos` espera texto livre, e uma lista quebraria o `re.split`.
- `objeto`: se o auditor não salvou `textos.objeto`, vale `[contrato.objeto]` (quando preenchido); senão o texto salvo.
- `documentacao_analisada`: se não salvou, vale o texto padrão **mais** "Normas técnicas consideradas: NBR … (descrição); …" (de `contrato.nbrs`) e "Documentos técnicos da edificação analisados: nome (tipo); …" (de `edificacao.documentos_tecnicos.itens`). Para saber se foi "salvo" usei `relatorio_conteudo_service._salvo` (função interna do serviço), porque `obter` devolve o merge já com os padrões.
- Obrigatórios (`validar_contexto_ltip`): `edificacao.nome`, `fiscal.nome`, `fiscal.crea`, `contrato.art_fiscalizacao` (o template imprime sem fallback).

**RFIP** (`rfip_pipeline.normalizar_contexto`): `inspecao`, `responsavel` (= fiscal do contrato, com `titulo_profissional`), `incluir_resumo` (conteúdo; padrão `true`), `ocorrencias` planas. Obrigatórios: `responsavel.nome`, `responsavel.crea` (rodapé do template; os demais campos têm '—').

**Comum:**
- As ocorrências saem por `seq_numero`; o pipeline agrupa por sistema com `sistema_ordem` e ordena dentro do sistema por `subsistema_ordem`.
- GUT e prioridade ausentes ficam `None` (o pipeline imprime '—' e só calcula a pontuação com as três notas); textos vazios viram '—' (DEC-33). Por isso `validar_obrigatorios` trata '—' como ausente: o contexto já normalizado continua detectando CREA ou ART faltando.
- `extrair_fotos`: **só a 1ª foto de cada ocorrência** (a ficha do LTIP e do RFIP mostra uma foto, `_storage_key_da_foto`). Fotos adicionais não são baixadas do storage.
- Contexto incompleto → 422 `ltip-contexto-incompleto` / `rfip-contexto-incompleto`, um `errors[].field` por campo (mecanismo da V1-02).

## Testes e comandos

Ambiente: o Python local não roda a suíte (mesmos motivos registrados na V1-01/V1-02: passlib/bcrypt e WeasyPrint sem GTK). Rodei num container descartável da imagem `05_infra-backend` (rede `garra-net`, `04_backend` do worktree montado em `/app`), contra um banco descartável `garra_tmp_v103` (criado com `createdb` no `garra-postgres`, migrado com `alembic upgrade head` até `a9c3e5f7b1d2` e removido no fim; o banco de dev não foi tocado). A imagem `05_infra-backend` tinha sido construída 52 min antes e o código vai montado, então **não rodei `docker compose build backend`**.

```
pytest tests/test_ltip_rfip_contexto.py tests/test_ltip_pipeline.py tests/test_rfip_pipeline.py \
       tests/test_rfo_contexto.py tests/test_relatorios_rfo_api.py \
       tests/test_relatorios_emissao_generica.py tests/test_rfo_art_execucao.py
→ 97 passed, 4 warnings (59 s)
ruff check .  → All checks passed!   (ruff instalado no container com pip)
```

`tests/test_ltip_rfip_contexto.py`: 16 passed. Cobre: contexto do banco passa em `normalizar_contexto` e renderiza o HTML (sem `None` nem `{{`) para LTIP e RFIP; legenda em rascunho de IA não aparece (nem no contexto, nem após normalizar); ordem por sistema/subsistema (a `ordem` do gabarito, não o nº); textos salvos vencem os padrões montados; `incluir_resumo`; 409 de tipo divergente; 422 sem CREA do fiscal (LTIP e RFIP, sem chamar o renderizador nem gravar no storage); `POST` com renderizador fake cria `Relatorio` tipo LTIP/RFIP versão `V01` com PDF e DOCX, baixando só a 1ª foto de cada ocorrência.

A suíte completa não foi rodada.

## PDF e DOCX reais (item 7)

Script `gera_reais.py` (em `$CLAUDE_JOB_DIR/tmp`, fora do repositório) rodou no mesmo container: criou o cenário de teste no banco, montou o contexto com `montar_contexto_*`, usou 2 fotos JPEG sintéticas de 1200×800 e chamou `gerar_pdf`/`gerar_docx` dos pipelines reais (WeasyPrint e docxtpl no container). Cenário: 3 ocorrências em 2 sistemas, 2 fotos. Tempos incluem só a geração, sem baixar fotos.

| Relatório | Formato | Páginas | Tempo | Tamanho |
|---|---|---|---|---|
| LTIP | PDF | 11 | 2,36 s | 102 398 bytes |
| LTIP | DOCX | n/d (o pipeline não conta) | 0,31 s | 93 811 bytes |
| RFIP | PDF | 4 | 1,90 s | 204 574 bytes |
| RFIP | DOCX | n/d | 0,28 s | 93 624 bytes |

Os arquivos ficaram em `$CLAUDE_JOB_DIR/tmp/out/` (não commitados: o cenário é sintético). Não abri os PDF/DOCX para conferência visual.

## Achados e propostas (para o fechamento de lote; não registradas em `00_docs/projeto`)

1. **Um contrato tem uma inspeção só** (`inspecoes.contrato_id` UNIQUE) e `inspecao.tipo` tem de ser igual ao tipo emitido (409). Portanto um LTIP e seu RFIP precisam de contratos/inspeções distintos. Se o produto quiser emitir o relatório fotográfico (RFIP) da mesma inspeção LTIP, é decisão de modelo (a V1-01 já deixa o conteúdo por tipo, DEC proposta 3).
2. **Só a 1ª foto por ocorrência** entra no relatório (herdado do template); fotos extras ficam sem uso. Se o cliente quiser todas, mudam pipelines e templates.
3. `data_emissao` do LTIP vai em `dd/mm/aaaa` no contexto (o RFIP e as vistorias não usam o campo no pipeline atual).
4. `00_docs/arquitetura.md` / `04_backend/README.md`: citar `contexto_comum`, `ltip_contexto`, `rfip_contexto` e os dois emissores novos.
