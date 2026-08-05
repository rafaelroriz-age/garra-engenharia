---
title: Backlog Kanban (Notion) — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
related:
  - 00_docs/projeto/backlog-tarefas.md
  - 00_docs/projeto/decisoes.md
  - .vscode/mcp.json
last_updated: 2026-07-27
---

# Backlog Kanban — espelho para o Notion (DEC-20 / ADR-11)

> Conteúdo pronto para ser criado como um banco de dados no Notion (visualização em quadro, no estilo de `Backlog / To do / In progress / Done`), assim que o servidor MCP `notion` for autenticado (ver [HT-12](backlog-tarefas-humanas.md#ht-12--autenticar-o-servidor-mcp-do-notion)). Até lá, este arquivo é a fonte de verdade local do board.
>
> Cada cartão = 1 tarefa de [backlog-tarefas.md](backlog-tarefas.md), com **ID**, **Requisitos/Decisões** e **Agente** como propriedades do banco de dados no Notion (colunas da view Tabela). A coluna aqui embaixo é a propriedade **Status** (agrupamento da view Quadro). Não duplica o conteúdo detalhado — sempre que `backlog-tarefas.md` mudar de status, atualizar este arquivo e (com o MCP conectado) o board real no Notion.
>
> **Critério de mapeamento de status → coluna:** ✅ Concluída → **Done**; 🟢 desbloqueada sem trabalho iniciado → **To do**; 🟢 (parcial)/parcialmente em execução → **In progress**; 🔴 bloqueada (B-01/B-02/depende de outra tarefa) → **Backlog**.

## Propriedades do banco de dados no Notion

| Propriedade | Tipo | Valores |
|---|---|---|
| Nome | Título | `BL-XX — <tarefa>` |
| Status | Select (agrupamento do Quadro) | `Backlog`, `To do`, `In progress`, `Done` |
| Requisitos/Decisões | Texto | Ex.: `RF-01`, `DEC-07` |
| Agente | Multi-select | `Engenheiro Backend`, `Engenheiro Frontend`, `Engenheiro DevOps`, `Engenheiro de Software`, `Gestor de Projeto` |
| Etapa | Select | `Etapa 0`, `Etapa 1/2`, `Etapa 3`, `Etapa 4`, `Etapa 4.5`, `Etapa 6/7` |

---

## 🔵 Backlog (10)

| ID | Tarefa | Requisitos/Decisões | Agente |
|---|---|---|---|
| BL-12 | Prototipagem do template HTML/CSS do RFO para PDF (WeasyPrint) | RF-06, RNF-03, DEC-01 | Prototipagem e Documentação para Cliente |
| BL-13 | Geração de DOCX do RFO via docxtpl | RF-06, DEC-04 | Engenheiro Backend |
| BL-15 | Regra de prioridade automática por Grau de Risco CMM | RN-04 | Engenheiro Backend |
| BL-17 | Prototipagem de templates HTML/CSS do LTIP + relatório fotográfico | RF-06, RN-11, RNF-03 | Prototipagem e Documentação para Cliente |
| BL-18 | Agendar e conduzir sessão de validação das 10 lacunas `[A ESCLARECER]` | — | Gestor de Projeto |
| BL-19 | Solicitar e receber arquivos `.docx` de template e logo em alta resolução | — | Gestor de Projeto |
| BL-32 | Portal do Cliente — dashboard e acompanhamento da auditoria | RF-13, RN-14 | Engenheiro Backend + Frontend |
| BL-33 | Portal do Cliente — documentos/relatórios do cliente | RF-13, RN-14 | Engenheiro Backend + Frontend |
| BL-34 | Legendas assistidas por IA (backend): `prompts_ia`, campos em `Foto`, Adapter `LegendaIAClient` | RF-15, RN-16, RN-17, DEC-21 | Engenheiro Backend |
| BL-35 | Legendas assistidas por IA (frontend): geração, revisão e aprovação da legenda sugerida | RF-15, RN-16, RN-17 | Engenheiro Frontend |

## 🟡 To do (7)

| ID | Tarefa | Requisitos/Decisões | Agente |
|---|---|---|---|
| BL-21 | Testes E2E dos fluxos RFO e LTIP | RNF-06 | Engenheiro de Software |
| BL-22 | Benchmark de geração de PDF/DOCX (200 páginas, 150+ fotos) | RNF-06, R-03 | Engenheiro de Software |
| BL-23 | Revisão de segurança OWASP Top 10 | RNF-05 | Engenheiro de Software |
| BL-27 | `docker-compose.prod.yml` + `nginx/nginx.conf` | DEC-14 | Engenheiro DevOps |
| BL-29 | `backup-db.sh` / `restore-db.sh` + agendamento | DEC-14, RNF-08 | Engenheiro DevOps |
| BL-30 | RBAC: campo `role`, vínculo `Responsavel.usuario_id`/`Contrato.contratante_id` | RF-13, RN-14, DEC-18 | Engenheiro Backend |
| BL-31 | Editor de anotação de fotos (setas, formas, texto, traço livre) | RF-14, RN-15, DEC-19 | Engenheiro Frontend |

## 🟠 In progress (5)

| ID | Tarefa | Requisitos/Decisões | Agente |
|---|---|---|---|
| BL-10 | Registro de Visitas do RFO (equipe, serviços, medições) | RF-03, RN-01, RN-02 | Engenheiro Backend + Frontend |
| BL-11 | Upload de fotos (clipboard paste + upload manual) | RF-05, RNF-02 | Engenheiro Backend + Frontend |
| BL-14 | CRUD de Ocorrências (sistema, subsistema, localização, classificação) | RF-04, RN-03, RN-05, RN-10 | Engenheiro Backend + Frontend |
| BL-16 | Dashboard de saúde por edificação/sistema predial | RF-07 | Engenheiro Backend + Frontend |
| BL-24 | Deploy de produção (Render) | Decisão de hospedagem | Engenheiro DevOps |

## 🟢 Done (13)

| ID | Tarefa | Requisitos/Decisões | Agente |
|---|---|---|---|
| BL-01 | Setup do ambiente de desenvolvimento (Docker Compose, PostgreSQL, MinIO) | DEC-02, DEC-07 | Engenheiro DevOps |
| BL-02 | Scaffold do backend FastAPI | DEC-05 | Engenheiro Backend |
| BL-03 | Scaffold do frontend Next.js 14 PWA | DEC-03, DEC-06, RNF-01 | Engenheiro Frontend |
| BL-04 | Modelagem de dados: SQLAlchemy 2 + migrations Alembic | DEC-07 | Engenheiro Backend |
| BL-05 | Seed do gabarito de sistemas prediais/subsistemas/anomalias | RF-10 | Engenheiro Backend |
| BL-06 | Autenticação JWT + bcrypt | RNF-05, DEC-05 | Engenheiro Backend |
| BL-07 | Storage service: MinIO/S3 (boto3) | RNF-07, DEC-02 | Engenheiro Backend |
| BL-08 | CRUD de Edificações | RF-01 | Engenheiro Backend + Frontend |
| BL-09 | CRUD de Contratos | RF-02, RF-12, RN-06, RN-09 | Engenheiro Backend + Frontend |
| BL-20 | Definir preferência de hospedagem (Render) | — | Gestor de Projeto |
| BL-25 | Repositório Git remoto no GitHub | DEC-14 | Engenheiro DevOps |
| BL-26 | `ci.yml` (lint, testes, build, scan Trivy) | DEC-14 | Engenheiro DevOps |
| BL-28 | `cd-staging.yml`/`cd-production.yml` (reavaliados) | DEC-14, DEC-17 | Engenheiro DevOps |

---

## Como publicar este board no Notion

1. Concluir [HT-12](backlog-tarefas-humanas.md#ht-12--autenticar-o-servidor-mcp-do-notion) (autenticar o servidor MCP `notion` via OAuth no VS Code).
2. Pedir ao agente para "criar o banco de dados no Notion a partir de `backlog-kanban.md`" — o agente usa as ferramentas do MCP Notion para: criar a página/banco de dados, configurar a propriedade `Status` (select) com as 4 opções acima, criar um cartão por linha das tabelas deste arquivo, e ativar a visualização em quadro (agrupada por `Status`) como view padrão.
3. Depois de criado, manter a sincronização é manual (reexecutar o passo 2 quando este arquivo mudar) — automação de sync contínuo está fora do escopo da DEC-20.
