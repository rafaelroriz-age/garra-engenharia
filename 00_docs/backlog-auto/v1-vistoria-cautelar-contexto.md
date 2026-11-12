# V1-04 · Emissão da Vistoria Cautelar a partir do banco (T60)

Contexto da Vistoria Cautelar montado do banco, validado e registrado como `Emissor` (V1-02). Com isso, `POST /api/v1/inspecoes/{id}/relatorios/VISTORIA_CAUTELAR` emite PDF + DOCX. Papel: Engenheiro Backend. Data: 2026-11-11. Branch: `worktree-backlog-T60` (commit local, sem push).

> **Nota de ambiente:** o worktree nasceu na base antiga `14ead2f` (lote D), sem nenhum dos arquivos citados na tarefa. A branch não tinha commits próprios e `14ead2f` é ancestral de `main`, então fiz `git merge --ff-only main` (até `7429900`) antes de começar. Nada foi reescrito.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `04_backend/app/services/report_generator/vistoria_cautelar_contexto.py` (novo) | `TIPO_VISTORIA_CAUTELAR`, `montar_contexto_vistoria_cautelar(db, inspecao_id)`, `validar_contexto_vistoria_cautelar(contexto)`, `extrair_fotos_vistoria_cautelar(contexto)`, `cidade_do_endereco(endereco)`. As consultas ficam no próprio arquivo: `contexto_comum.py` não existe na `main` e não foi criado. |
| `04_backend/app/services/relatorio_service.py` | Importa o módulo acima e registra `Emissor(tipo="VISTORIA_CAUTELAR", pipeline="vistoria_cautelar_pipeline")` logo depois do RFO; docstring do módulo atualizada. |
| `04_backend/tests/test_vistoria_cautelar_contexto.py` (novo) | 13 testes: 7 de unidade, 6 com banco (4 de serviço, 2 de API). |

Pipeline, templates, `layout.json`, textos padrão e `01_output-context/` **não** foram alterados.

## Mapeamento banco → contexto

| Contexto (`vistoria_cautelar_pipeline.normalizar_contexto`) | Origem |
|---|---|
| `responsavel.{nome, crea, email, telefone, titulo_profissional, qualificacoes}` | `contrato.fiscal` (`Responsavel`, colunas da V1-01). `qualificacoes` vazias ou nulas são descartadas. |
| `assinatura_storage_key` | `fiscal.assinatura_storage_key`; a chave só entra no contexto quando preenchida |
| `obra.descricao` | `contrato.objeto` |
| `edificacao.nome` | `edificacao.nome` |
| `data_emissao` | `dados.data_emissao`; padrão: `date.today()` (ISO) |
| `local_emissao` | `dados.local_emissao`; padrão: `cidade_do_endereco(edificacao.endereco)`; se não achar, `None` (o pipeline imprime `—`) |
| `conteudo.*` | `relatorio_conteudo_service.obter(...).dados["textos"]`: textos padrão (`textos_padrao/vistoria_cautelar.json`, placeholders preenchidos) + o que o auditor salvou (deep merge) |
| `conteudo.datas_das_vistorias` | se o texto salvo/padrão estiver vazio: frase montada de `dados.datas_vistorias` ("As vistorias foram realizadas em 05/10/2026 e 19/10/2026.") |
| `complementos.parecer_tecnico` | `dados.parecer` |
| `tabelas.identificacao` | `Edificacao`: Endereço, CEP, Tipologia, Sistema construtivo, Pavimentos, Área total construída (`1.234,50 m²`). Valor nulo vira `—` no pipeline. |
| `tabelas.plano_de_correcoes_remanescentes` | uma linha por ocorrência (ordem `seq_numero`): `item` = `seq_numero`, `localizacao`, `descricao_da_pendencia` = `descricao`, `metodologia_corretiva_indicada` = `dados.metodologia_corretiva[str(ocorrencia.id)]` ou `—` |
| `sistemas[]` | ocorrências agrupadas por `sistema_id`, em ordem de `(SistemaPredial.ordem, nome)`: `nome`, `constatacoes` = descrições não vazias das ocorrências, `fundamentacao_tecnica` = `dados.fundamentacao_tecnica[str(sistema_id)]` ou `[]` |
| `figuras[]` | fotos das ocorrências (ocorrência por `seq_numero`, foto por `ordem`, nulos ao fim), numeradas 1..n: `{numero, legenda, storage_key}`. `legenda` = `legenda_para_relatorio(foto)` ou `None`. A `legenda_ia_sugerida` nunca entra (DEC-37 DP-9), e a foto continua no relatório. |
| `capa_fundo_storage_key` | não vem do banco (não há coluna). `extrair_fotos` a inclui se alguém a puser no contexto. |
| `inspecao.{id, tipo, status}` | informativo |

`montar_contexto_vistoria_cautelar` repete as checagens do RFO: 404 `inspecao-nao-encontrada` e 409 `inspecao-nao-vistoria_cautelar` (o mesmo sufixo que `emitir_relatorio` gera).

### Validação (422 por campo)

`CAMPOS_OBRIGATORIOS_VISTORIA_CAUTELAR`: `responsavel.nome`, `responsavel.crea` (fiscal) e `complementos.parecer_tecnico` (parecer). Ausente = `None` ou texto em branco. Na API vira `422 .../vistoria_cautelar-contexto-incompleto`, com um item `{"field": ..., "message": ...}` por campo em `errors`. `responsavel.nome` é NOT NULL no banco, mas foi mantido para o validador valer também com contexto montado fora do banco.

### Fotos baixadas (`extrair_fotos`)

`{figura.storage_key}` ∪ `{assinatura_storage_key}` ∪ `{capa_fundo_storage_key}` (só as presentes). Chave ausente no storage → 409 `foto-ausente-no-storage` (V1-02). Isso vale também para a assinatura: se o fiscal tem `assinatura_storage_key` e o arquivo não existe no MinIO, a emissão falha.

## Testes (`tests/test_vistoria_cautelar_contexto.py`)

- Unidade: emissor registrado com as 3 funções e o pipeline; `extrair_fotos` com figuras, figura sem chave, assinatura e capa; validador apontando `responsavel.crea`/`complementos.parecer_tecnico` e o contexto vazio; `cidade_do_endereco` (4 casos).
- Banco (cenário: fiscal com CREA, título, qualificação e assinatura; edificação completa; 2 sistemas; 3 ocorrências; 3 fotos, uma com sugestão de IA em `rascunho` e `legenda` nula):
  - `test_contexto_do_banco_passa_no_normalizar_contexto`: confere cada campo do mapeamento, a ordem dos sistemas por `SistemaPredial.ordem` (não por `seq_numero`), a numeração das figuras, `normalizar_contexto` e `renderizar_html` com JPEGs sintéticos (o HTML não contém `None` nem `{{` e contém o parecer e a metodologia);
  - `test_legenda_nao_aprovada_nao_entra`: a sugestão de IA não aparece em lugar nenhum do contexto, e a figura sai com `legenda=None`, que vira `—` no normalizado;
  - `test_metodologia_corretiva_por_ocorrencia`: a linha 2 tem a metodologia salva e as linhas 1 e 3 têm `—`;
  - `test_sem_conteudo_salvo_usa_padroes_e_falta_parecer`: sem `RelatorioConteudo`, os padrões entram e o validador aponta só o parecer;
  - `test_post_sem_parecer_retorna_422`: API, 422 com `errors[].field == ["complementos.parecer_tecnico"]`, sem renderizar e sem gravar nada;
  - `test_post_cria_versao_1_com_renderizador_fake`: `PUT .../conteudo/VISTORIA_CAUTELAR` seguido de `POST .../relatorios/VISTORIA_CAUTELAR` → 201, `V01`, `relatorios/{id}/vistoria_cautelar-v01.{pdf,docx}` no storage fake, renderizador chamado para pdf e docx com as 4 fotos (3 figuras + assinatura).

## Comandos e saídas

Ambiente: Postgres/MinIO do `05_infra` no ar (`garra-postgres`). O banco de dev (`garra_engenharia`) está em `f7c2a9d4e6b1`, atrás do head, e **não foi tocado**. Criei um banco descartável `garra_tmp_v104` no mesmo servidor (`createdb`), migrei com `alembic upgrade head` (→ `a9c3e5f7b1d2 (head)`) e o apaguei (`dropdb`) no fim. O `.env` usado pelo compose é o do checkout principal (`--env-file`); o worktree não tem `.env` e nada foi commitado.

```text
cd 05_infra
docker compose --env-file <checkout principal>/05_infra/.env build backend        # OK (05_infra-backend)
docker compose ... run --rm --no-deps -e POSTGRES_DB=garra_tmp_v104 \
  -v <worktree>/04_backend:/app backend sh -c 'python -m pytest ...'
```

**Atenção (ambiente compartilhado):** a imagem `05_infra-backend` é a mesma tag para todos os worktrees. Entre o meu `build` e a geração real, outro job paralelo a reconstruiu com o código dele (`obter_emissor` listava `RFO, VISTORIA_RESIDENCIAL`, sem `VISTORIA_CAUTELAR`). Por isso, todas as rodadas abaixo montam o `04_backend` **deste worktree** em `/app` (`-v ...:/app`). Assim o código testado é este, qualquer que seja a imagem.

```text
pytest tests/test_vistoria_cautelar_contexto.py tests/test_vistoria_cautelar_pipeline.py tests/test_relatorios_rfo_api.py
→ 35 passed   (13 + 9 + 13; inclui o teste de PDF real do pipeline, que no Windows era pulado)

pytest tests/test_relatorios_emissao_generica.py tests/test_relatorio_conteudo.py tests/test_legenda_relatorio_vistorias.py
→ 53 passed   (20 + 23 + 10; regressão da V1-02, da V1-01 e da BL-36)
```

A suíte completa (`pytest` sem argumentos) **não** foi rodada.

`ruff check .` (ruff 0.15.1, `ruff.toml` do backend) → **10 erros, todos pré-existentes e em arquivos não tocados**, os mesmos registrados em V1-01/V1-02: `alembic/versions/e5a1f0c2b7d4_...dec_48.py` (UP035, I001, 3× UP007), `tests/test_fotos_storage_key_unico.py` (3× F811), `tests/test_portal_versoes_relatorio.py` (I001), `tests/test_relatorio_unicidade.py` (I001). Nos 3 arquivos desta tarefa: `All checks passed!`.

### Geração real de PDF e DOCX (container)

Script descartável (fora do repositório, em `$CLAUDE_JOB_DIR/tmp/v104/gerar_real.py`). Ele grava no `garra_tmp_v104` um cenário sintético com uma ocorrência de `localizacao` e `descricao` nulas e uma foto com IA em rascunho, salva o conteúdo (parecer, 2 datas, metodologia de 1 ocorrência, fundamentação de 1 sistema), monta o contexto via `obter_emissor("VISTORIA_CAUTELAR")` e chama `vistoria_cautelar_pipeline.gerar_pdf`/`gerar_docx` com JPEGs 640×480. O texto do PDF foi extraído com `pypdf` e o do DOCX com `python-docx` (parágrafos, tabelas, cabeçalhos e rodapés).

```text
validar: []
fotos: 4
pdf:  render_html 0.076 s, conversao_pdf 3.447 s, total 3.523 s, 19 páginas, 743 906 bytes
docx: render_e_salvar 0.218 s, 100 264 bytes
PDF  {'caracteres': 23721, 'None': 0, '{{': 0, '{%': 0, 'SUGESTAO-IA': 0, 'parecer': False, 'metodologia': True, 'local Goiânia-GO': True, 'datas 05/10/2026': True, 'fiscal': True, 'legenda manual': True}
DOCX {'caracteres': 18209, 'None': 0, '{{': 0, '{%': 0, 'SUGESTAO-IA': 0, 'parecer': True, 'metodologia': True, 'local Goiânia-GO': True, 'datas 05/10/2026': True, 'fiscal': True, 'legenda manual': True}
```

No PDF, a busca do parecer pela frase inteira deu `False` porque a extração quebra a linha do título. O texto extraído mostra `10.1. Parecer Técnico — Recebimento provisório com` / `ressalvas`, ou seja, o parecer está impresso. A linha da ocorrência sem dados saiu `3 — — —` na tabela 10.2. Nenhuma ocorrência de `None`, `{{` ou `{%` em nenhum dos dois formatos.

## Observações e decisões propostas (para o fechamento de lote; nada registrado em `00_docs/projeto/`)

1. **Cidade de emissão derivada do endereço.** `Edificacao` não tem campo de cidade. O padrão de `local_emissao` vem de um segmento `Cidade-UF`/`Cidade - UF`/`Cidade/UF` do endereço livre (separado por vírgulas). Sem esse padrão, sai `—` (`—, 11 de novembro de 2026.`). Proposta: coluna `cidade`/`uf` em `Edificacao` (ou exigir `local_emissao` no conteúdo) numa tarefa futura.
2. **Obrigatórios = fiscal (nome, CREA) + parecer.** O restante sai com `—` ou com texto padrão. Proposta de DEC: estender DEC-47 à Vistoria Cautelar com essa lista.
3. **Todas as ocorrências entram no Plano de Correções (10.2) e nos sistemas (9.x)**, sem filtro por `situacao`. Se o laudo precisar listar só as pendências (ex.: `situacao != "Conforme"`), o filtro deve ser decidido com o cliente.
4. **Foto com legenda não aprovada continua no relatório, com legenda `—`** (no PDF: `Figura 2 - — Fonte: Autor.`). Isso segue a regra da BL-36 (só `legenda` é impressa). Se o cliente preferir omitir a figura ou bloquear a emissão enquanto houver IA em rascunho, `sinalizar_fotos_ia_em_rascunho` já existe e não tem consumidor.
5. **Assinatura obrigatória no storage quando cadastrada.** `assinatura_storage_key` preenchida e arquivo ausente → 409 na emissão. Ainda não há rota de upload de assinatura (V1-01, proposta 5).
6. **Ambiente:** a tag `05_infra-backend` é compartilhada entre worktrees paralelos (ver "Atenção" acima). Para lotes paralelos, convém testar sempre com `-v <worktree>/04_backend:/app` ou usar uma tag por worktree.

## Para o fechamento de lote (00_docs)

- `00_docs/projeto/backlog-tarefas.md`, `backlog-kanban.md`, `status.md`: V1-04 entregue; `VISTORIA_CAUTELAR` emitível pela rota genérica.
- `04_backend/README.md` / `00_docs/arquitetura.md`: tipos registrados em `EMISSORES` passam a ser RFO e VISTORIA_CAUTELAR (mais o que os outros lotes registrarem).
- `00_docs/projeto/decisoes.md`: avaliar as propostas 1 a 4. `riscos.md`: item 6 (imagem Docker compartilhada).
