---
title: Backlog de Tarefas — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
last_updated: 2026-07-19
---

# Backlog de Tarefas

> Ordenado de forma crescente por complexidade/dependência (mais simples e desbloqueadas primeiro). Cada item referencia a Etapa do [ciclo-de-vida.md](ciclo-de-vida.md), os RF/RNF/RN de [estudo-do-contexto.md](../estudo-do-contexto.md) e o status de bloqueio.
>
> Tarefas que só um humano pode executar (decisões de negócio, comunicação com o cliente, credenciais, atos jurídicos) estão em [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md), não neste arquivo.

**Legenda de status:** ✅ Concluída (executada e validada) | 🟢 Desbloqueada (pronta para iniciar) | 🟢 (parcial) Uma camada pronta, outra pendente | 🔴 Bloqueada (B-01 lacunas / B-02 templates / B-03 hospedagem)

## Etapa 0 — Fundação Técnica

| # | Tarefa | Requisitos/Decisões | Status | Agente | Prompt |
|---|---|---|---|---|---|
| BL-01 | Setup do ambiente de desenvolvimento: Docker Compose com PostgreSQL 16 + MinIO, `.env.example` | DEC-02, DEC-07 | ✅ Concluída (2026-07-17) — ver [05_infra/README.md](../../05_infra/README.md) e [status.md](status.md#artefatos-entregues) | Engenheiro DevOps | [14-setup-ambiente-desenvolvimento.prompt.md](../../.github/prompts/14-setup-ambiente-desenvolvimento.prompt.md) |
| BL-02 | Scaffold do backend FastAPI: estrutura de pastas (`app/api`, `app/models`, `app/schemas`, `app/services`, `app/core`), healthcheck, config via variáveis de ambiente | DEC-05, arquitetura.md §7 | ✅ Concluída (2026-07-17) — ver [04_backend/README.md](../../04_backend/README.md) | Engenheiro Backend | [15-scaffold-backend-fastapi.prompt.md](../../.github/prompts/15-scaffold-backend-fastapi.prompt.md) |
| BL-03 | Scaffold do frontend Next.js 14 PWA: estrutura de rotas (App Router), `manifest.json`, Tailwind + shadcn/ui, tela inicial | DEC-03, DEC-06, RNF-01 | ✅ Concluída (2026-07-17) — ver [03_frontend/README.md](../../03_frontend/README.md) | Engenheiro Frontend | [16-scaffold-frontend-nextjs-pwa.prompt.md](../../.github/prompts/16-scaffold-frontend-nextjs-pwa.prompt.md) |
| BL-04 | Modelagem de dados: modelos SQLAlchemy 2 + migrations Alembic para as 14 entidades do diagrama ER | DEC-07, arquitetura.md §3 | ✅ Concluída (2026-07-17) — ver [04_backend/README.md](../../04_backend/README.md) | Engenheiro Backend | [17-modelagem-dados-migrations.prompt.md](../../.github/prompts/17-modelagem-dados-migrations.prompt.md) |
| BL-05 | Seed do gabarito de sistemas prediais, subsistemas, tipos de anomalia/falha e localizações a partir de `RFO_INSPECAO.md` | RF-10 | ✅ Concluída (2026-07-17) — ver [04_backend/README.md](../../04_backend/README.md) e DEC-13 em [decisoes.md](decisoes.md) | Engenheiro Backend | [18-seed-gabarito-sistemas-prediais.prompt.md](../../.github/prompts/18-seed-gabarito-sistemas-prediais.prompt.md) |
| BL-06 | Autenticação JWT + bcrypt: cadastro/login, proteção de rotas | RNF-05, DEC-05 | ✅ Concluída (2026-07-19) — ver [04_backend/README.md](../../04_backend/README.md) e DEC-15 em [decisoes.md](decisoes.md) | Engenheiro Backend | [19-autenticacao-jwt.prompt.md](../../.github/prompts/19-autenticacao-jwt.prompt.md) |
| BL-07 | Storage service: cliente MinIO/S3 (boto3) com upload/download/URL pré-assinada para fotos | RNF-07, DEC-02 | ✅ Concluída (2026-07-20) — ver [04_backend/README.md](../../04_backend/README.md#storage-service-minios3-bl-07) | Engenheiro Backend | [20-storage-service-minio.prompt.md](../../.github/prompts/20-storage-service-minio.prompt.md) |

## Etapa 3 — Incremento RFO

| # | Tarefa | Requisitos/Decisões | Status | Agente | Prompt Sugerido | Observação |
|---|---|---|---|---|---|---|
| BL-08 | CRUD de Edificações (backend + frontend) | RF-01 | 🟢 | Engenheiro Backend + Engenheiro Frontend | [21-crud-edificacoes.prompt.md](../../.github/prompts/21-crud-edificacoes.prompt.md) | **Backend concluído (2026-07-20)** — endpoints, repository/service e testes prontos (ver [04_backend/README.md](../../04_backend/README.md)); frontend pendente |
| BL-09 | CRUD de Contratos com múltiplas empresas executoras e NBRs | RF-02, RF-12, RN-06, RN-09 | 🟢 | Engenheiro Backend + Engenheiro Frontend | [22-crud-contratos.prompt.md](../../.github/prompts/22-crud-contratos.prompt.md) | **Backend concluído (2026-07-20)** — criação/atualização em cascata de executoras/NBRs + Inspeção 1:1; frontend pendente |
| BL-10 | Registro de Visitas do RFO (equipe, serviços, medições) | RF-03, RN-01, RN-02 | 🟢 | Engenheiro Backend + Engenheiro Frontend | [23-registro-visitas-rfo.prompt.md](../../.github/prompts/23-registro-visitas-rfo.prompt.md) | **Backend concluído (2026-07-20)** — `seq_numero` sequencial automático; frontend pendente |
| BL-11 | Upload de fotos (clipboard paste + upload manual) vinculado a Visitas | RF-05, RNF-02 (parcial) | 🟢 | Engenheiro Backend + Engenheiro Frontend | [24-upload-fotos-lightshot.prompt.md](../../.github/prompts/24-upload-fotos-lightshot.prompt.md) (depende de BL-07 para storage) | **Backend concluído (2026-07-20)** — reprocessamento Pillow (A08), sem URL de cliente (A10); Opção C fora de escopo v1.0; frontend pendente |
| BL-12 | Prototipagem do template HTML/CSS do RFO para PDF (WeasyPrint), usando `Relatorio_de_Fiscalizacao.md` como referência visual | RF-06, RNF-03, DEC-01 | 🔴 B-02 (parcial) | Prototipagem e Documentação para Cliente | `05-prototipagem.prompt.md` | Pode iniciar com fidelidade aproximada; validação final exige `.docx` original |
| BL-13 | Geração de DOCX do RFO via docxtpl | RF-06, DEC-04 | 🔴 B-02 | Engenheiro Backend | `06-backend.prompt.md` (aguardando destravar) | Bloqueada até recebimento do `.docx` original do cliente |

## Etapa 4 — Incremento LTIP + Dashboard

| # | Tarefa | Requisitos/Decisões | Status | Agente | Prompt Sugerido | Observação |
|---|---|---|---|---|---|---|
| BL-14 | CRUD de Ocorrências (sistema, subsistema, localização, classificação) | RF-04, RN-03, RN-05, RN-10 | 🟢 (parcial) | Engenheiro Backend + Engenheiro Frontend | [25-crud-ocorrencias.prompt.md](../../.github/prompts/25-crud-ocorrencias.prompt.md) | **Frontend implementado e testado (2026-07-21)** — listagem com filtros, formulário de classificação completa, upload de fotos e painel RN-10 em `03_frontend/app/inspecoes/[id]/ocorrencias/`; aguardando os endpoints do Engenheiro Backend (`/inspecoes/{id}/ocorrencias`, `/ocorrencias/{id}`). Contrato de enums (Situação/Classificação/Grau de Risco) assumido pelo frontend, a confirmar quando o backend for implementado |
| BL-15 | Regra de prioridade automática por Grau de Risco CMM (RN-04) | RN-04 | 🔴 B-01 | Engenheiro Backend | `06-backend.prompt.md` (aguardando destravar) | Depende de confirmação se o engenheiro pode sobrescrever manualmente (lacuna #10 relacionada) |
| BL-16 | Dashboard de saúde por edificação/sistema predial | RF-07 | 🟢 (parcial) | Engenheiro Backend + Engenheiro Frontend | [26-dashboard-saude-edificacao.prompt.md](../../.github/prompts/26-dashboard-saude-edificacao.prompt.md) | **Frontend implementado e testado (2026-07-21)** — `03_frontend/app/dashboard/page.tsx` consumindo `GET /edificacoes/{id}/dashboard`; aguardando a agregação CQRS + cache Redis do Engenheiro Backend |
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
| BL-21 | Testes E2E dos fluxos RFO e LTIP | RNF-06 | 🟢 (depende das etapas 3 e 4) | Engenheiro de Software | [29-testes-e2e-rfo-ltip.prompt.md](../../.github/prompts/29-testes-e2e-rfo-ltip.prompt.md) |
| BL-22 | Benchmark de geração de PDF/DOCX (200 páginas, 150+ fotos) | RNF-06, R-03 | 🟢 (depende de BL-12/BL-13) | Engenheiro de Software (com apoio do Engenheiro DevOps para infraestrutura de teste) | [30-benchmark-geracao-relatorios.prompt.md](../../.github/prompts/30-benchmark-geracao-relatorios.prompt.md) |
| BL-23 | Revisão de segurança OWASP Top 10 (auth, upload de arquivos, injeção) | RNF-05 | 🟢 (depende das etapas anteriores) | Engenheiro de Software (ou Engenheiro Backend) | [31-revisao-seguranca-owasp.prompt.md](../../.github/prompts/31-revisao-seguranca-owasp.prompt.md) |
| BL-24 | Deploy de produção (Docker Compose ou nuvem) | DEC decisão de hospedagem | 🔴 B-03 (baixo impacto) | Engenheiro DevOps | `12-devops.prompt.md` |

### Gestão de Configuração (Git / CI-CD) — derivado de DEC-14

| # | Tarefa | Requisitos/Decisões | Status | Agente | Prompt |
|---|---|---|---|---|---|
| BL-25 | Inicializar repositório Git local, primeiro commit e criação do repositório remoto no GitHub | DEC-14 | ✅ Concluída (2026-07-19) — repositório privado `rafaelroriz-age/garra-engenharia`, branch `main` publicada. **Falta ação manual do usuário:** configurar a proteção de branch em Settings > Branches (Seção 1.4 do plano) — não automatizável pelas ferramentas disponíveis | Engenheiro DevOps | `12-devops.prompt.md` — ver `00_docs/projeto/plano-gestao-configuracao.md` |
| BL-26 | Implementar `.github/workflows/ci.yml` (lint, testes, build de imagens, scan Trivy) | DEC-14 | ✅ Concluída (2026-07-19) — workflow publicado em `.github/workflows/ci.yml`. **Falta ação manual:** marcar `ci.yml` como status check obrigatório na proteção de branch | Engenheiro DevOps | `12-devops.prompt.md` |
| BL-27 | Implementar `docker-compose.prod.yml` + `nginx/nginx.conf` (HTTPS, reverse proxy) | DEC-14, mesmo escopo de BL-24 | 🟢 | Engenheiro DevOps | [27-docker-compose-prod-nginx.prompt.md](../../.github/prompts/27-docker-compose-prod-nginx.prompt.md) |
| BL-28 | Implementar `cd-staging.yml` e `cd-production.yml` (deploy via SSH + GHCR, aprovação manual em produção) | DEC-14 | 🔴 B-03 (depende de BL-26, BL-27 e decisão de hospedagem) | Engenheiro DevOps | `12-devops.prompt.md` (aguardando destravar) |
| BL-29 | Implementar `05_infra/backup/backup-db.sh` e `restore-db.sh` + agendamento | DEC-14, RNF-08 | 🟢 (depende de BL-27) | Engenheiro DevOps | [28-backup-restore-scripts.prompt.md](../../.github/prompts/28-backup-restore-scripts.prompt.md) |

## Resumo

- **Tarefas concluídas:** BL-01 (ambiente de desenvolvimento), BL-02 (scaffold backend FastAPI), BL-03 (scaffold frontend Next.js PWA), BL-04 (modelagem de dados: modelos SQLAlchemy + migrations Alembic), BL-05 (seed do gabarito de sistemas prediais/subsistemas/tipos de anomalia/falha/localizações), BL-06 (autenticação JWT + bcrypt), BL-07 (storage service MinIO/S3 via boto3), BL-25 (repositório Git remoto criado e publicado), BL-26 (workflow `ci.yml` publicado) — evidências em `05_infra/README.md`, `04_backend/README.md`, `03_frontend/README.md`, DEC-13/DEC-14/DEC-15 em [decisoes.md](decisoes.md) e [status.md](status.md#artefatos-entregues).
- **Tarefas parcialmente concluídas (frontend pronto, backend pendente):** BL-14 e BL-16 — telas implementadas e testadas (build + lint + smoke test em 2026-07-21: `03_frontend/app/inspecoes/[id]/ocorrencias/`, `03_frontend/app/dashboard/page.tsx`), aguardando os endpoints correspondentes do Engenheiro Backend para integração ponta a ponta.
- **Tarefas 100% desbloqueadas para início imediato:** BL-08 a BL-11, BL-27, BL-29.
- **Tarefas bloqueadas por B-01 (lacunas):** BL-15, BL-18.
- **Tarefas bloqueadas por B-02 (templates):** BL-12 (parcial), BL-13, BL-17, BL-19.
- **Tarefas bloqueadas por B-03 (hospedagem):** BL-20, BL-24 (impacto baixo, não impede desenvolvimento), BL-28 (depende de BL-26/BL-27).
- **Prompts criados em 2026-07-17** (`.github/prompts/14-*` a `19-*`): cobrem BL-01 a BL-06, a base da Etapa 0, todas 100% desbloqueadas.
- **Plano de Gestão de Configuração** (2026-07-19): `00_docs/projeto/plano-gestao-configuracao.md` (DEC-14) define estratégia de Git (trunk-based, Conventional Commits, SemVer), pipelines CI/CD via GitHub Actions e estratégia de deploy/rollback/backup — gera BL-25 a BL-29.
- **Prompts especializados criados em 2026-07-19** (`.github/prompts/20-*` a `31-*`): substituem as referências genéricas (`06-backend`/`07-frontend`/`08-engenheiro-software`/`12-devops`) para as tarefas 🟢 desbloqueadas sem prompt dedicado — BL-07 (`20-storage-service-minio`), BL-08 (`21-crud-edificacoes`), BL-09 (`22-crud-contratos`), BL-10 (`23-registro-visitas-rfo`), BL-11 (`24-upload-fotos-lightshot`), BL-14 (`25-crud-ocorrencias`), BL-16 (`26-dashboard-saude-edificacao`), BL-27 (`27-docker-compose-prod-nginx`), BL-29 (`28-backup-restore-scripts`), BL-21 (`29-testes-e2e-rfo-ltip`), BL-22 (`30-benchmark-geracao-relatorios`), BL-23 (`31-revisao-seguranca-owasp`). As tarefas 🔴 bloqueadas (BL-12, BL-13, BL-15, BL-17, BL-18 a BL-20, BL-24, BL-28) mantiveram os prompts genéricos/"aguardando destravar", pois seu conteúdo depende das lacunas (B-01) ou templates (B-02) ainda não resolvidos.
