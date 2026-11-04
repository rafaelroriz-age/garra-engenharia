---
title: Dicionário de dados — banco PostgreSQL
type: knowledge
status: draft
owner: Garra Engenharia
related:
  - 04_backend/app/models/
  - 04_backend/alembic/versions/
  - 00_docs/arquitetura.md
  - 00_docs/estudo-do-contexto.md
tags: [dados, banco, postgresql, sqlalchemy, alembic, modelo-de-dados]
last_updated: 2026-11-03
---

<!-- ai-summary
System: as 18 tabelas do banco, coluna a coluna, como estão nos modelos SQLAlchemy e nas 6 migrations Alembic.
Flow: app/models/*.py (fonte) -> alembic/versions/*.py (schema aplicado) -> este documento.
Owner: Garra Engenharia.
Status: draft — levantado na D04 (2026-11-03) sobre o head d3b7c9e4f1a2.
-->

# Dicionário de dados

Fonte: os modelos em `04_backend/app/models/*.py` e as migrations em `04_backend/alembic/versions/`. O diagrama ER resumido está em [arquitetura.md](arquitetura.md) §3; este documento é a referência coluna a coluna.

**Convenções gerais (valem para todas as tabelas)**

- Chave primária `id` do tipo `UUID`, gerada na aplicação (`default=uuid.uuid4`).
- Nenhuma FK declara `ondelete` (`grep -n ondelete 04_backend/alembic/versions/*.py` → vazio): o banco não apaga em cascata.
- Os campos com valores fechados (situação, grau de risco, perfil etc.) são `VARCHAR` sem `CHECK` no banco. A validação, quando existe, está na aplicação, e a coluna "Valores" diz onde.
- `created_at`: `TIMESTAMP WITH TIME ZONE`, `NOT NULL`, padrão `now()` no banco (migration `c22d4029c062`).
- "Nulo" = coluna aceita `NULL` (`mapped_column(..., nullable=...)`).

## Migrations (ordem de aplicação)

| Revisão | Arquivo | O que faz |
|---|---|---|
| `c22d4029c062` | `initial_schema_14_entidades_do_diagrama_.py` | cria as 14 tabelas do ER (BL-04) |
| `8e2467ad6a92` | `gabarito_tipos_anomalia_falha_.py` | cria `localizacoes`, `tipos_anomalia`, `tipos_falha` (BL-05) |
| `ab22bfcbdd0a` | `usuario_auth_jwt_bl_06.py` | cria `usuarios` e o índice único `ix_usuarios_email` (BL-06) |
| `5f9f3cb4d87f` | `rbac_role_contratante_bl_30.py` | `usuarios.role`, `responsaveis.usuario_id` (único), `contratos.contratante_id` (BL-30) |
| `7c1a4e0b93d5` | `autoria_criado_por_perfil_auxiliar_bl_42.py` | `criado_por_id` em `visitas`, `ocorrencias` e `fotos` (BL-42, DEC-27) |
| `d3b7c9e4f1a2` | `prioridade_sugerida_sobrescrita_bl_15.py` | `ocorrencias.prioridade_sugerida`, `prioridade_ajustada_por_id`, `prioridade_ajustada_em` (BL-15, RN-04, DEC-29) |

## Cadastros

### `edificacoes` (`models/edificacao.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `nome` | VARCHAR | não | |
| `endereco` | VARCHAR | não | |
| `cep` | VARCHAR | sim | |
| `tipologia` | VARCHAR | sim | |
| `sistema_construtivo` | VARCHAR | sim | |
| `descricao_pavimentos` | TEXT | sim | |
| `area_total_m2` | FLOAT | sim | |
| `documentos_tecnicos` | JSONB | sim | `{"itens": [...]}`, preenchido por `POST /edificacoes/{id}/documentos` (`app/api/v1/edificacoes.py:109-113`, DEC-16) |
| `created_at` | TIMESTAMPTZ | não | |

### `responsaveis` (`models/responsavel.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `nome` | VARCHAR | não | |
| `tipo` | VARCHAR | não | texto livre no schema (`app/schemas/responsavel.py`); valor observado `fiscal` (`tests/test_contratos.py:68`, `seed_benchmark_rfo.py:149`). Papéis previstos: fiscal, responsável legal, RTE, contratante (DEC-23) |
| `cpf_cnpj` | VARCHAR | sim | |
| `crea` | VARCHAR | sim | |
| `email` | VARCHAR | sim | |
| `telefone` | VARCHAR | sim | |
| `usuario_id` | UUID | sim | FK `usuarios.id`, **único** (`uq_responsaveis_usuario_id`). Liga o login de um cliente ao seu `Responsavel`; o portal filtra por ele (`app/api/deps.py`, `get_current_cliente_responsavel`) |

### `usuarios` (`models/usuario.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `nome` | VARCHAR | não | |
| `email` | VARCHAR | não | índice único `ix_usuarios_email` |
| `senha_hash` | VARCHAR | não | bcrypt (`app/core/security.py`) |
| `ativo` | BOOLEAN | não | padrão `True` na aplicação |
| `role` | VARCHAR | não | `auditor` (padrão no banco), `auxiliar` ou `cliente` (`app/schemas/usuario.py:16`, `Literal`); ADR-09, ADR-14 |

### `contratos` (`models/contrato.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `edificacao_id` | UUID | não | FK `edificacoes.id` |
| `fiscal_id` | UUID | não | FK `responsaveis.id` |
| `contratante_id` | UUID | sim | FK `responsaveis.id`; define o escopo do portal do cliente |
| `numero` | VARCHAR | não | |
| `tipo_servico` | VARCHAR | não | o frontend usa `RFO`, `LTIP`, `VISTORIA_CAUTELAR`, `VISTORIA_RESIDENCIAL`, `RFIP` (`03_frontend/lib/types.ts:66-71`); o backend não valida |
| `objeto` | TEXT | sim | |
| `data_inicio` | DATE | sim | |
| `prazo_dias` | INTEGER | sim | |
| `art_fiscalizacao` | VARCHAR | sim | |
| `observacoes_gerais` | TEXT | sim | |
| `status` | VARCHAR | não | padrão do schema `em_andamento` (`app/schemas/contrato.py:76`); o tipo do frontend usa `EM_ANDAMENTO`/`CONCLUIDO`/`CANCELADO` (`lib/types.ts:73`). A diferença de caixa não é tratada no código |
| `created_at` | TIMESTAMPTZ | não | |

### `contrato_executores` (`models/contrato_executor.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `contrato_id` | UUID | não | FK `contratos.id` |
| `responsavel_legal_id` | UUID | não | FK `responsaveis.id` |
| `rte_id` | UUID | sim | FK `responsaveis.id` (responsável técnico da execução) |
| `razao_social` | VARCHAR | não | |
| `cnpj` | VARCHAR | não | |
| `endereco` | VARCHAR | sim | |
| `art_execucao` | VARCHAR | sim | |

### `contrato_nbrs` (`models/contrato_nbr.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `contrato_id` | UUID | não | FK `contratos.id` |
| `codigo_nbr` | VARCHAR | não | |
| `descricao` | VARCHAR | sim | |

## Inspeção e campo

### `inspecoes` (`models/inspecao.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `contrato_id` | UUID | não | FK `contratos.id`, **único**: uma inspeção por contrato, criada junto com o contrato (`app/repositories/contrato_repository.py:74`) |
| `tipo` | VARCHAR | não | copiado de `contratos.tipo_servico` na criação |
| `status` | VARCHAR | não | `em_andamento` na criação (`contrato_repository.py:74`) |
| `created_at` | TIMESTAMPTZ | não | |

### `visitas` (`models/visita.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `inspecao_id` | UUID | não | FK `inspecoes.id` |
| `data` | DATE | não | RN-01: uma visita por dia de obra (`visita_repository.py:26`) |
| `servicos_executados` | TEXT | sim | |
| `observacoes` | TEXT | sim | |
| `seq_numero` | INTEGER | não | sequencial dentro da inspeção, calculado como `max + 1` (`visita_repository.py:25-28`) |
| `criado_por_id` | UUID | sim | FK `usuarios.id`; autoria vinda do token, nunca do payload (DEC-27) |

### `visita_mao_obras` (`models/visita_mao_obra.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `visita_id` | UUID | não | FK `visitas.id` |
| `funcao` | VARCHAR | não | texto livre (não há tabela de funções; ver "Previsto e não implementado") |
| `quantidade` | INTEGER | não | |

### `visita_medicoes` (`models/visita_medicao.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `visita_id` | UUID | não | FK `visitas.id` |
| `descricao` | VARCHAR | não | |
| `quantidade` | FLOAT | não | |
| `unidade` | VARCHAR | não | |

### `ocorrencias` (`models/ocorrencia.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `inspecao_id` | UUID | não | FK `inspecoes.id` |
| `sistema_id` | UUID | não | FK `sistemas_prediais.id` |
| `subsistema_id` | UUID | sim | FK `subsistemas.id` |
| `localizacao` | VARCHAR | sim | texto (não é FK para `localizacoes`) |
| `situacao` | VARCHAR | não | `CONFORME` / `NAO_CONFORME` (`03_frontend/lib/ocorrencia-enums.ts:13`); obrigatória (`ocorrencia_service.py:91`) |
| `classificacao` | VARCHAR | não | `ANOMALIA`, `FALHA`, `ANOMALIA_FALHA`, `NAO_SE_APLICA` (`ocorrencia-enums.ts`); RN-05: `ANOMALIA*` exige `tipo_anomalia`, `*FALHA` exige `tipo_falha` (`ocorrencia_service.py:95-98`) |
| `tipo_anomalia` | VARCHAR | sim | texto (não é FK para `tipos_anomalia`) |
| `tipo_falha` | VARCHAR | sim | texto (não é FK para `tipos_falha`) |
| `grau_risco` | VARCHAR | sim no banco | CMM: `MINIMO`, `MEDIO`, `CRITICO`; a aplicação rejeita outro valor, inclusive vazio (`ocorrencia_service.py:99`) |
| `prioridade` | INTEGER | sim | 0 a 5 (RN-05, `ocorrencia_service.py:102`). Se não for informada, recebe a `prioridade_sugerida` |
| `prioridade_sugerida` | INTEGER | sim | RN-04/DEC-29: `CRITICO`=5, `MEDIO`=3, `MINIMO`=1; 0 se `situacao=CONFORME` ou `classificacao=NAO_SE_APLICA` (`ocorrencia_service.py:13`, `:106-116`) |
| `prioridade_ajustada_por_id` | UUID | sim | FK `usuarios.id`; preenchida só quando a prioridade efetiva difere da sugerida (`_resolver_prioridade`, `:119-133`) |
| `prioridade_ajustada_em` | TIMESTAMPTZ | sim | instante do ajuste, mesma regra |
| `descricao` | TEXT | sim | |
| `gut_gravidade` | FLOAT | sim | GUT gravado como enviado; o produto G×U×T não é calculado nem gravado (`grep` sem resultado em `app/`) |
| `gut_urgencia` | FLOAT | sim | idem |
| `gut_tendencia` | FLOAT | sim | idem |
| `seq_numero` | INTEGER | não | sequencial dentro da inspeção (`ocorrencia_repository.py:123-125`) |
| `criado_por_id` | UUID | sim | FK `usuarios.id` (DEC-27) |

Não há `created_at` em `ocorrencias`, `visitas`, `relatorios` nem nas tabelas filhas.

### `fotos` (`models/foto.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `ocorrencia_id` | UUID | sim | FK `ocorrencias.id` |
| `visita_id` | UUID | sim | FK `visitas.id` |
| `storage_key` | VARCHAR | não | chave no bucket, `fotos/<uuid>.<ext>` (`app/services/foto_service.py:36-44`) |
| `url_publica` | VARCHAR | sim | |
| `legenda` | TEXT | sim | |
| `origem` | VARCHAR | não | o frontend envia `upload` ou `lightshot` (`components/foto-upload.tsx:92`); o tipo prevê também `camera` (`lib/types.ts:185`) |
| `ordem` | INTEGER | sim | |
| `created_at` | TIMESTAMPTZ | não | |
| `criado_por_id` | UUID | sim | FK `usuarios.id` (DEC-27) |

### `relatorios` (`models/relatorio.py`)

| Coluna | Tipo | Nulo | Observação |
|---|---|---|---|
| `id` | UUID | não | PK |
| `inspecao_id` | UUID | não | FK `inspecoes.id` |
| `versao` | VARCHAR | não | |
| `tipo` | VARCHAR | não | |
| `status` | VARCHAR | não | |
| `pdf_key` | VARCHAR | sim | chave do PDF no bucket |
| `docx_key` | VARCHAR | sim | chave do DOCX no bucket |
| `emitido_em` | TIMESTAMPTZ | sim | |

Hoje nenhuma rota da API cria registros em `relatorios`; só o script de benchmark cria (`app/scripts/benchmark_relatorio_geracao.py:143-147`, com `tipo="RFO"` e `status="concluido"`). O portal lê esta tabela (`app/services/portal_service.py`).

## Gabarito (dados mestre)

Populadas por `python -m app.scripts.seed_gabarito` a partir de `00_docs/convertidos/RFO_INSPECAO.md` (`app/scripts/rfo_gabarito_parser.py`). Expostas por `GET /api/v1/sistemas-prediais` e `/gabarito/*` (`app/api/v1/dados_mestre.py`).

| Tabela | Colunas | Observação |
|---|---|---|
| `sistemas_prediais` (`models/sistema_predial.py`) | `id` UUID PK; `nome` VARCHAR não nulo; `ordem` INTEGER não nulo | |
| `subsistemas` (`models/subsistema.py`) | `id` UUID PK; `sistema_id` UUID não nulo, FK `sistemas_prediais.id`; `nome` VARCHAR não nulo; `ordem` INTEGER não nulo | |
| `tipos_anomalia` (`models/tipo_anomalia.py`) | `id` UUID PK; `nome` VARCHAR não nulo, **único**; `ordem` INTEGER não nulo | |
| `tipos_falha` (`models/tipo_falha.py`) | `id` UUID PK; `nome` VARCHAR não nulo, **único**; `ordem` INTEGER não nulo | |
| `localizacoes` (`models/localizacao.py`) | `id` UUID PK; `nome` VARCHAR não nulo, **único**; `ordem` INTEGER não nulo | |

## Relações

```text
edificacoes 1──N contratos 1──1 inspecoes 1──N visitas 1──N visita_mao_obras
                    │                 │            ├──N visita_medicoes
                    ├──N contrato_executores       └──N fotos
                    └──N contrato_nbrs  ├──N ocorrencias 1──N fotos
                                        └──N relatorios
responsaveis 1──N contratos (fiscal_id, contratante_id) · 1──N contrato_executores (responsavel_legal_id, rte_id)
usuarios 1──0..1 responsaveis (usuario_id) · 1──N visitas/ocorrencias/fotos (criado_por_id) · 1──N ocorrencias (prioridade_ajustada_por_id)
sistemas_prediais 1──N subsistemas · 1──N ocorrencias ; subsistemas 1──N ocorrencias
```

## Previsto e não implementado

Aparecem em [arquitetura.md](arquitetura.md) (ER e contratos de API), mas não existem nos modelos nem nas migrations (`grep -n "prompt_ia\|aprovado_por_id" 04_backend/app/models/*.py` → vazio):

- tabela `prompts_ia` (`PROMPT_IA`) e, em `fotos`, os campos `legenda_bruta`, `legenda_ia_sugerida`, `nivel_certeza_ia`, `status_validacao_ia`, `alertas_ia`, `pendencias_ia`, `prompt_ia_id`, `aprovado_por_id`, `aprovado_em` (ADR-12, RF-15; provedor de IA pendente, B-04 em `00_docs/projeto/status.md`);
- lista de funções de mão de obra (`/gabarito/funcoes-mao-obra`): não há tabela; `visita_mao_obras.funcao` é texto livre;
- campos de auditoria `updated_at` (citados em `arquitetura.md` §10.1, A09): nenhuma tabela tem.
