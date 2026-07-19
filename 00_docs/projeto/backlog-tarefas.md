---
title: Backlog de Tarefas — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-07-17
---

# Backlog de Tarefas

> Ordenado de forma crescente por complexidade/dependência (mais simples e desbloqueadas primeiro). Cada item referencia a Etapa do [ciclo-de-vida.md](ciclo-de-vida.md), os RF/RNF/RN de [estudo-do-contexto.md](../estudo-do-contexto.md) e o status de bloqueio.

**Legenda de status:** ✅ Concluída (executada e validada) | 🟢 Desbloqueada (pronta para iniciar) | 🔴 Bloqueada (B-01 lacunas / B-02 templates / B-03 hospedagem)

## Etapa 0 — Fundação Técnica

| # | Tarefa | Requisitos/Decisões | Status | Agente | Prompt |
|---|---|---|---|---|---|
| BL-01 | Setup do ambiente de desenvolvimento: Docker Compose com PostgreSQL 16 + MinIO, `.env.example` | DEC-02, DEC-07 | ✅ Concluída (2026-07-17) — ver [05_infra/README.md](../../05_infra/README.md) e [status.md](status.md#artefatos-entregues) | Engenheiro DevOps | [14-setup-ambiente-desenvolvimento.prompt.md](../../.github/prompts/14-setup-ambiente-desenvolvimento.prompt.md) |
| BL-02 | Scaffold do backend FastAPI: estrutura de pastas (`app/api`, `app/models`, `app/schemas`, `app/services`, `app/core`), healthcheck, config via variáveis de ambiente | DEC-05, arquitetura.md §7 | ✅ Concluída (2026-07-17) — ver [04_backend/README.md](../../04_backend/README.md) | Engenheiro Backend | [15-scaffold-backend-fastapi.prompt.md](../../.github/prompts/15-scaffold-backend-fastapi.prompt.md) |
| BL-03 | Scaffold do frontend Next.js 14 PWA: estrutura de rotas (App Router), `manifest.json`, Tailwind + shadcn/ui, tela inicial | DEC-03, DEC-06, RNF-01 | ✅ Concluída (2026-07-17) — ver [03_frontend/README.md](../../03_frontend/README.md) | Engenheiro Frontend | [16-scaffold-frontend-nextjs-pwa.prompt.md](../../.github/prompts/16-scaffold-frontend-nextjs-pwa.prompt.md) |
| BL-04 | Modelagem de dados: modelos SQLAlchemy 2 + migrations Alembic para as 14 entidades do diagrama ER | DEC-07, arquitetura.md §3 | ✅ Concluída (2026-07-17) — ver [04_backend/README.md](../../04_backend/README.md) | Engenheiro Backend | [17-modelagem-dados-migrations.prompt.md](../../.github/prompts/17-modelagem-dados-migrations.prompt.md) |
| BL-05 | Seed do gabarito de sistemas prediais, subsistemas, tipos de anomalia/falha e localizações a partir de `RFO_INSPECAO.md` | RF-10 | ✅ Concluída (2026-07-17) — ver [04_backend/README.md](../../04_backend/README.md) e DEC-13 em [decisoes.md](decisoes.md) | Engenheiro Backend | [18-seed-gabarito-sistemas-prediais.prompt.md](../../.github/prompts/18-seed-gabarito-sistemas-prediais.prompt.md) |
| BL-06 | Autenticação JWT + bcrypt: cadastro/login, proteção de rotas | RNF-05, DEC-05 | 🟢 | Engenheiro Backend | [19-autenticacao-jwt.prompt.md](../../.github/prompts/19-autenticacao-jwt.prompt.md) |
| BL-07 | Storage service: cliente MinIO/S3 (boto3) com upload/download/URL pré-assinada para fotos | RNF-07, DEC-02 | 🟢 | Engenheiro Backend | Não criado — usar `06-backend.prompt.md` (genérico) ou gerar `20-storage-service-minio.prompt.md` com `09-criar-prompt.prompt.md` |

## Etapa 3 — Incremento RFO

| # | Tarefa | Requisitos/Decisões | Status | Agente | Prompt Sugerido | Observação |
|---|---|---|---|---|---|---|
| BL-08 | CRUD de Edificações (backend + frontend) | RF-01 | 🟢 | Engenheiro Backend + Engenheiro Frontend | `06-backend.prompt.md` + `07-frontend.prompt.md` | Não depende de templates; telas de cadastro genéricas |
| BL-09 | CRUD de Contratos com múltiplas empresas executoras e NBRs | RF-02, RF-12, RN-06, RN-09 | 🟢 | Engenheiro Backend + Engenheiro Frontend | `06-backend.prompt.md` + `07-frontend.prompt.md` | Depende de BL-04 e BL-08 |
| BL-10 | Registro de Visitas do RFO (equipe, serviços, medições) | RF-03, RN-01, RN-02 | 🟢 | Engenheiro Backend + Engenheiro Frontend | `06-backend.prompt.md` + `07-frontend.prompt.md` | Depende de BL-09 |
| BL-11 | Upload de fotos (clipboard paste + upload manual) vinculado a Visitas | RF-05, RNF-02 (parcial) | 🟢 | Engenheiro Backend + Engenheiro Frontend | `06-backend.prompt.md` + `07-frontend.prompt.md` (depende de BL-07 para storage) | Opção C (pasta monitorada) fora de escopo v1.0 |
| BL-12 | Prototipagem do template HTML/CSS do RFO para PDF (WeasyPrint), usando `Relatorio_de_Fiscalizacao.md` como referência visual | RF-06, RNF-03, DEC-01 | 🔴 B-02 (parcial) | Prototipagem e Documentação para Cliente | `05-prototipagem.prompt.md` | Pode iniciar com fidelidade aproximada; validação final exige `.docx` original |
| BL-13 | Geração de DOCX do RFO via docxtpl | RF-06, DEC-04 | 🔴 B-02 | Engenheiro Backend | `06-backend.prompt.md` (aguardando destravar) | Bloqueada até recebimento do `.docx` original do cliente |

## Etapa 4 — Incremento LTIP + Dashboard

| # | Tarefa | Requisitos/Decisões | Status | Agente | Prompt Sugerido | Observação |
|---|---|---|---|---|---|---|
| BL-14 | CRUD de Ocorrências (sistema, subsistema, localização, classificação) | RF-04, RN-03, RN-05, RN-10 | 🟢 | Engenheiro Backend + Engenheiro Frontend | `06-backend.prompt.md` + `07-frontend.prompt.md` | Não depende de lacunas para o CRUD básico |
| BL-15 | Regra de prioridade automática por Grau de Risco CMM (RN-04) | RN-04 | 🔴 B-01 | Engenheiro Backend | `06-backend.prompt.md` (aguardando destravar) | Depende de confirmação se o engenheiro pode sobrescrever manualmente (lacuna #10 relacionada) |
| BL-16 | Dashboard de saúde por edificação/sistema predial | RF-07 | 🟢 (depende de BL-14) | Engenheiro Backend + Engenheiro Frontend | `06-backend.prompt.md` + `07-frontend.prompt.md` | Não bloqueado tecnicamente, mas depende de ocorrências existirem |
| BL-17 | Prototipagem de templates HTML/CSS do LTIP + relatório fotográfico por sistema | RF-06, RN-11, RNF-03 | 🔴 B-02 | Prototipagem e Documentação para Cliente | `05-prototipagem.prompt.md` (aguardando destravar) | Mesma restrição de BL-12 |

## Etapa 1/2 — Ações de Gestão (não são tarefas de engenharia)

| # | Tarefa | Responsável | Agente | Prompt/Ação | Status |
|---|---|---|---|---|---|
| BL-18 | Agendar e conduzir sessão de validação das 10 lacunas `[A ESCLARECER]` | Gestor de Projeto | Gestor de Projeto / Arquiteto de Soluções (este modo) | Ação de gestão direta — sem prompt técnico; usar `estudo-do-contexto.md` §9 como pauta | 🔴 B-01 (ação necessária) |
| BL-19 | Solicitar e receber arquivos `.docx` de template (RFO, LTIP, Vistoria Cautelar, RFIP) e logo em alta resolução | Gestor de Projeto | Gestor de Projeto / Arquiteto de Soluções (este modo) | Ação de gestão direta — comunicação com cliente | 🔴 B-02 (ação necessária) |
| BL-20 | Definir preferência de hospedagem (local vs. nuvem) | Gestor de Projeto | Gestor de Projeto / Arquiteto de Soluções (este modo), com apoio técnico do Engenheiro DevOps | Ação de gestão direta; consultar `12-devops.prompt.md` para opções técnicas | 🔴 B-03 (baixo impacto, mitigado por Docker Compose agnóstico) |

## Etapa 6/7 — Integração, Testes e Deploy

| # | Tarefa | Requisitos/Decisões | Status | Agente | Prompt |
|---|---|---|---|---|---|
| BL-21 | Testes E2E dos fluxos RFO e LTIP | RNF-06 | 🟢 (depende das etapas 3 e 4) | Engenheiro de Software | `08-engenheiro-software.prompt.md` |
| BL-22 | Benchmark de geração de PDF/DOCX (200 páginas, 150+ fotos) | RNF-06, R-03 | 🟢 (depende de BL-12/BL-13) | Engenheiro de Software (com apoio do Engenheiro DevOps para infraestrutura de teste) | `08-engenheiro-software.prompt.md` + `12-devops.prompt.md` |
| BL-23 | Revisão de segurança OWASP Top 10 (auth, upload de arquivos, injeção) | RNF-05 | 🟢 (depende das etapas anteriores) | Engenheiro de Software (ou Engenheiro Backend) | `08-engenheiro-software.prompt.md` |
| BL-24 | Deploy de produção (Docker Compose ou nuvem) | DEC decisão de hospedagem | 🔴 B-03 (baixo impacto) | Engenheiro DevOps | `12-devops.prompt.md` |

### Gestão de Configuração (Git / CI-CD) — derivado de DEC-14

| # | Tarefa | Requisitos/Decisões | Status | Agente | Prompt |
|---|---|---|---|---|---|
| BL-25 | Inicializar repositório Git local, primeiro commit e criação do repositório remoto no GitHub | DEC-14 | 🟢 Desbloqueada | Engenheiro DevOps | `12-devops.prompt.md` — ver `00_docs/projeto/plano-gestao-configuracao.md` |
| BL-26 | Implementar `.github/workflows/ci.yml` (lint, testes, build de imagens, scan Trivy) | DEC-14 | 🟢 (depende de BL-25) | Engenheiro DevOps | `12-devops.prompt.md` |
| BL-27 | Implementar `docker-compose.prod.yml` + `nginx/nginx.conf` (HTTPS, reverse proxy) | DEC-14, mesmo escopo de BL-24 | 🟢 | Engenheiro DevOps | `12-devops.prompt.md` |
| BL-28 | Implementar `cd-staging.yml` e `cd-production.yml` (deploy via SSH + GHCR, aprovação manual em produção) | DEC-14 | 🔴 B-03 (depende de BL-26, BL-27 e decisão de hospedagem) | Engenheiro DevOps | `12-devops.prompt.md` |
| BL-29 | Implementar `05_infra/backup/backup-db.sh` e `restore-db.sh` + agendamento | DEC-14, RNF-08 | 🟢 (depende de BL-27) | Engenheiro DevOps | `12-devops.prompt.md` |

## Resumo

- **Tarefas concluídas:** BL-01 (ambiente de desenvolvimento), BL-02 (scaffold backend FastAPI), BL-03 (scaffold frontend Next.js PWA), BL-04 (modelagem de dados: modelos SQLAlchemy + migrations Alembic), BL-05 (seed do gabarito de sistemas prediais/subsistemas/tipos de anomalia/falha/localizações) — evidências em `05_infra/README.md`, `04_backend/README.md`, `03_frontend/README.md`, DEC-13 em [decisoes.md](decisoes.md) e [status.md](status.md#artefatos-entregues).
- **Tarefas 100% desbloqueadas para início imediato:** BL-06 a BL-11, BL-14, BL-16 (parcial), BL-25 a BL-27, BL-29.
- **Tarefas bloqueadas por B-01 (lacunas):** BL-15, BL-18.
- **Tarefas bloqueadas por B-02 (templates):** BL-12 (parcial), BL-13, BL-17, BL-19.
- **Tarefas bloqueadas por B-03 (hospedagem):** BL-20, BL-24 (impacto baixo, não impede desenvolvimento), BL-28 (depende de BL-26/BL-27).
- **Prompts criados nesta rodada** (`.github/prompts/14-*` a `19-*`): cobrem BL-01 a BL-06, a base da Etapa 0, todas 100% desbloqueadas.
- **Plano de Gestão de Configuração** (2026-07-19): `00_docs/projeto/plano-gestao-configuracao.md` (DEC-14) define estratégia de Git (trunk-based, Conventional Commits, SemVer), pipelines CI/CD via GitHub Actions e estratégia de deploy/rollback/backup — gera BL-25 a BL-29.
