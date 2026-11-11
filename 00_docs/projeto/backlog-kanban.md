---
title: Backlog Kanban (Notion) — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
related:
  - 00_docs/projeto/backlog-tarefas.md
  - 00_docs/projeto/decisoes.md
  - .vscode/mcp.json
last_updated: 2026-09-17
---

# Backlog Kanban — espelho para o Notion (DEC-20 / ADR-11)

> **Board real criado em 2026-08-07** (HT-12 concluída): banco de dados "Backlog — Garra Engenharia" no Notion — https://app.notion.com/p/c5c276e8a13041499be0017833efb379 — com a view **Quadro** agrupada por `Status` e 52 cartões (BL-01 a BL-40 + HT-01 a HT-12, estas com `Etapa = "Tarefa humana (HT)"`). Este arquivo continua sendo o espelho local; a sincronização entre os dois é manual (DEC-20).
>
> Cada cartão = 1 tarefa de [backlog-tarefas.md](backlog-tarefas.md), com **ID**, **Requisitos/Decisões** e **Agente** como propriedades do banco de dados no Notion (colunas da view Tabela). A coluna aqui embaixo é a propriedade **Status** (agrupamento da view Quadro). Não duplica o conteúdo detalhado — sempre que `backlog-tarefas.md` mudar de status, atualizar este arquivo e o board real no Notion.
>
> **Critério de mapeamento de status → coluna:** ✅ Concluída → **Done**; 🟢 desbloqueada sem trabalho iniciado → **To do**; 🟢 (parcial)/parcialmente em execução → **In progress**; 🔴 bloqueada (B-04 ou depende de outra tarefa) → **Backlog**. B-01 (lacunas) foi encerrado em 2026-09-17 e não bloqueia mais nenhum cartão.

## Propriedades do banco de dados no Notion

| Propriedade | Tipo | Valores |
|---|---|---|
| Nome | Título | `BL-XX — <tarefa>` |
| Status | Select (agrupamento do Quadro) | `Backlog`, `To do`, `In progress`, `Done` |
| Requisitos/Decisões | Texto | Ex.: `RF-01`, `DEC-07` |
| Agente | Multi-select | `Engenheiro Backend`, `Engenheiro Frontend`, `Engenheiro DevOps`, `Engenheiro de Software`, `Gestor de Projeto` |
| Etapa | Select | `Etapa 0`, `Etapa 1/2`, `Etapa 3`, `Etapa 4`, `Etapa 4.5`, `Etapa 6/7` |

---

## 🔵 Backlog (7)

| ID | Tarefa | Requisitos/Decisões | Agente |
|---|---|---|---|
| BL-19 | Confirmar versão vigente dos originais em `01_output-context/` | — | Gestor de Projeto |
| BL-34 | Legendas assistidas por IA (backend): `prompts_ia`, campos em `Foto`, Adapter `LegendaIAClient` — 🟡 T25 (endpoints com cliente Fake; falta o adapter, B-04); T33 (aprovação só do auditor, invalidação) e T35 (limite de taxa 429, teto e saneamento da saída; DEC-42, proposta) | RF-15, RN-16, RN-17, DEC-21 | Engenheiro Backend |
| BL-35 | Legendas assistidas por IA (frontend): geração, revisão e aprovação da legenda sugerida — 🟡 T26 (painel pronto, testado com API mockada; falta backend real, B-04); T34 (sem «Aprovar» para o auxiliar e aviso de invalidação) | RF-15, RN-16, RN-17 | Engenheiro Frontend |
| BL-36 | Extensão da modelagem de dados para legendas assistidas por IA — ✅ T22 (migration `f7c2a9d4e6b1`) | RF-15, RN-16, RN-17, DEC-21 | Engenheiro Backend |
| BL-37 | Storage/metadata do fluxo de legendas assistidas por IA — ✅ T23 (`prompt_ia_service.py`, `LegendaIAClient` + Fake) | RF-15, RN-16, RN-17 | Engenheiro Backend |
| BL-38 | Integração do upload/edição de fotos com a geração de legendas por IA — 🟡 T24 (RFO) e T37 (Cautelar e Residencial); T36 (LTIP e RFIP); falta o alerta de fotos IA em rascunho | RF-15, RN-16, RN-17, BL-11 | Engenheiro Backend + Frontend |
| BL-39 | Integração do editor de anotação com o fluxo de aprovação de legendas por IA — 🟡 T38 (botão «Anotar foto»; anotação gera foto nova) | RF-15, RN-16, RN-17, BL-31 | Engenheiro Frontend |

## 🟡 To do (6)

| ID | Tarefa | Requisitos/Decisões | Agente |
|---|---|---|---|
| BL-15 | Prioridade da Ocorrência: sugestão pelo Grau de Risco + sobrescrita rastreável (desbloqueada por DEC-29) | RN-04, RN-05, DEC-29 | Engenheiro Backend |
| BL-23 | Revisão de segurança OWASP Top 10 — ✅ (2ª passada T29, 2026-11-05: 9 achados SEG-IA abertos nos endpoints de legenda IA) | RNF-05 | Engenheiro de Software |
| BL-27 | `docker-compose.prod.yml` + `nginx/nginx.conf` | DEC-14 | Engenheiro DevOps |
| BL-29 | `backup-db.sh` / `restore-db.sh` + agendamento (verificado com stubs, T42) | DEC-14, RNF-08 | Engenheiro DevOps |
| BL-32 | Portal do Cliente — dashboard e acompanhamento da auditoria (E2E, T41) | RF-13, RN-14 | Engenheiro Backend + Frontend |
| BL-33 | Portal do Cliente — documentos/relatórios (download real aguarda B-02) (E2E, T41) | RF-13, RN-14 | Engenheiro Backend + Frontend |

## 🟠 In progress (5)

| ID | Tarefa | Requisitos/Decisões | Agente |
|---|---|---|---|
| BL-10 | Registro de Visitas do RFO (equipe, serviços, medições) — T15: 18 lacunas; T21 corrigiu (L15 aberta, migration `e5a1c3f7b9d2`) | RF-03, RN-01, RN-02 | Engenheiro Backend + Frontend |
| BL-11 | Upload de fotos (clipboard paste + upload manual) — T16: 9 lacunas; T19 corrigiu 8 (faltam `UNIQUE(storage_key)` e URL pré-assinada; T31: `origem` do vínculo em enum fechado) | RF-05, RNF-02 | Engenheiro Backend + Frontend |
| BL-14 | CRUD de Ocorrências (sistema, subsistema, localização, classificação) — regras revisadas (T06); correções L1–L7 aplicadas (T08), testes ainda não rodados (sem PostgreSQL) | RF-04, RN-03, RN-05, RN-10 | Engenheiro Backend + Frontend |
| BL-16 | Dashboard de saúde por edificação/sistema predial | RF-07 | Engenheiro Backend + Frontend |
| BL-24 | Deploy de produção (Render) — faltam `POSTGRES_PASSWORD`/`JWT_SECRET_KEY` (LEGENDA_IA_* no compose/render, T40) | HT-04, DEC-22 | Engenheiro DevOps |

## 🟢 Done (22)

| ID | Tarefa | Requisitos/Decisões | Agente |
|---|---|---|---|
| BL-18 | Sessão de validação das lacunas `[A ESCLARECER]` — B-01 encerrado | DEC-26/27/28, DEC-29 | Gestor de Projeto |
| BL-01 | Setup do ambiente de desenvolvimento (Docker Compose, PostgreSQL, MinIO) | DEC-02, DEC-07 | Engenheiro DevOps |
| BL-02 | Scaffold do backend FastAPI | DEC-05 | Engenheiro Backend |
| BL-03 | Scaffold do frontend Next.js 14 PWA | DEC-03, DEC-06, RNF-01 | Engenheiro Frontend |
| BL-04 | Modelagem de dados: SQLAlchemy 2 + migrations Alembic — revisão de integração p/ legendas IA feita (T14) | DEC-07 | Engenheiro Backend |
| BL-05 | Seed do gabarito de sistemas prediais/subsistemas/anomalias | RF-10 | Engenheiro Backend |
| BL-06 | Autenticação JWT + bcrypt | RNF-05, DEC-05 | Engenheiro Backend |
| BL-07 | Storage service: MinIO/S3 (boto3) — T32: relatório de órfãos em dry-run | RNF-07, DEC-02 | Engenheiro Backend |
| BL-08 | CRUD de Edificações | RF-01 | Engenheiro Backend + Frontend |
| BL-09 | CRUD de Contratos | RF-02, RF-12, RN-06, RN-09 | Engenheiro Backend + Frontend |
| BL-42 | RBAC — perfil `auxiliar` (escrita limitada de dados de campo + autoria `criado_por_id`) | RN-18, DEC-27 | Engenheiro Backend + Frontend |
| BL-20 | Definir preferência de hospedagem (Render) | — | Gestor de Projeto |
| BL-25 | Repositório Git remoto no GitHub | DEC-14 | Engenheiro DevOps |
| BL-26 | `ci.yml` (lint, testes, build, scan Trivy) (ruff zerado e fixado em 0.15.1, T43; lint ainda não bloqueante, DEC-46) | DEC-14 | Engenheiro DevOps |
| BL-28 | `cd-staging.yml`/`cd-production.yml` (reavaliados) | DEC-14, DEC-17 | Engenheiro DevOps |
| BL-21 | Testes E2E dos fluxos RFO e LTIP (Playwright) | RNF-06, DEC-23 | Engenheiro de Software |
| BL-22 | Benchmark de geração de PDF/DOCX (191 páginas, 570 fotos) — re-medido (T17): LTIP violava RNF-06; T20 reduziu para 11,6 s (239 fotos) e 19,3 s (~200 páginas) | RNF-06, R-03 | Engenheiro de Software |
| BL-30 | RBAC: `role`, `Responsavel.usuario_id`, `Contrato.contratante_id` | RF-13, RN-14, DEC-18 | Engenheiro Backend |
| BL-31 | Editor de anotação de fotos (Fabric.js) | RF-14, RN-15, DEC-19 | Engenheiro Frontend |
| BL-40 | Template DOCX do Contrato de Prestação de Serviços | Administrativo | Engenheiro Backend |
| BL-12 | Prototipagem do template HTML/CSS do RFO para PDF (WeasyPrint) — template do RFIP entregue em 2026-11-04 (T13), `rfip_pipeline.py` entregue (T18); faltam mapeamento banco → contexto e conferência visual (HT-09) | RF-06, RNF-03, DEC-01 | Prototipagem e Documentação para Cliente |
| BL-13 | Geração de DOCX do RFO via docxtpl | RF-06, DEC-04 | Engenheiro Backend |

---

## Sincronização com o Notion

O board já existe (link no topo deste arquivo). A sincronização permanece **manual**: quando `backlog-tarefas.md` mudar, atualize este arquivo e peça ao agente para refletir a mudança no Notion (o MCP `notion` já está autenticado). Automação de sync contínuo continua fora do escopo da DEC-20.
3. Depois de criado, manter a sincronização é manual (reexecutar o passo 2 quando este arquivo mudar) — automação de sync contínuo está fora do escopo da DEC-20.
