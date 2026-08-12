---
title: Plano de Gestão de Configuração — Sistema de Automação de Relatórios Prediais
type: gestao
status: aprovado
owner: Garra Engenharia
related:
  - 00_docs/arquitetura.md
  - 00_docs/projeto/decisoes.md
  - 00_docs/projeto/backlog-tarefas.md
  - 05_infra/README.md
tags: [devops, git, ci-cd, deploy, versionamento, seguranca]
last_updated: 2026-07-19
---

# Plano de Gestão de Configuração (Git, CI/CD, Deploy)

> Define como o código é versionado, integrado, empacotado e implantado. Complementa `00_docs/arquitetura.md` (stack e ADRs) e `05_infra/README.md` (execução local). Referência de governança de decisões: `decisoes.md` DEC-14.

## 1. Estrutura de Repositório

**Modelo:** monorepo único no GitHub (`garra-engenharia`), contendo `00_docs/` a `05_infra/` e `.github/`. Justificativa: equipe pequena (1 engenheiro + agentes), forte acoplamento entre frontend/backend/infra nesta fase, e histórico único facilita rastrear uma feature ponta-a-ponta (fatia vertical, conforme `ciclo-de-vida.md`).

Não versionar: `.env`, `.env.*` (exceto `.env.example`), `node_modules/`, `.next/`, `.venv/`, `__pycache__/`, volumes Docker — já cobertos pelo `.gitignore` existente na raiz.

### 1.1 Branching — Trunk-Based simplificado, com branches dedicadas por serviço/ambiente (DEC-17)

- 4 branches de longa duração, cada uma servindo de gatilho de deploy de UM serviço no Render (o conteúdo do monorepo é o mesmo em todas — sem histórico filtrado, sem quebrar DEC-09):
  - `main_back` — produção do backend (`garra-backend` em `render.yaml`)
  - `main_front` — produção do frontend (`garra-frontend`)
  - `staging_back` — staging do backend (`garra-backend-staging`)
  - `staging_front` — staging do frontend (`garra-frontend-staging`)
- Todas as 4 protegidas (ver 1.4): merge exige PR + CI verde na branch correspondente.
- `main`/`staging` (nomes anteriores à DEC-17) continuam existindo no repositório, mas não estão mais conectadas a nenhum serviço do Render — usadas apenas como branch de integração intermediária, se o fluxo de trabalho do time preferir revisar ali antes de promover para as 4 branches de serviço.
- Branches de trabalho de vida curta (idealmente < 3 dias), a partir da branch de serviço/ambiente alvo:
  - `feat/<slug>` — nova funcionalidade (ex.: `feat/bl-06-auth-jwt`)
  - `fix/<slug>` — correção de bug
  - `chore/<slug>` — infra, dependências, configuração
  - `docs/<slug>` — apenas documentação (`00_docs/`)
- Uma mudança que afeta front e back ao mesmo tempo pode exigir 2 PRs (um por branch-alvo) ou merge nas duas branches — decisão tomada por PR, não automatizada.
- Sem `develop`/`release/*` — o backlog (`backlog-tarefas.md`) já cumpre o papel de plano de releases; branches longas de release adicionariam overhead desproporcional ao porte da equipe (mesmo racional de DEC-08).
- Rebase (não merge commit) da branch de feature sobre a branch-alvo antes de abrir PR, para manter histórico linear; merge do PR via **squash merge** (1 commit por PR).

### 1.2 Convenção de Commits — Conventional Commits

```
<tipo>(<escopo opcional>): <descrição curta no imperativo>

[corpo opcional explicando o porquê]

[rodapé opcional: Refs BL-XX, RF-XX, RN-XX]
```

Tipos permitidos: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`, `perf`. Escopo recomendado = pasta de topo (`backend`, `frontend`, `infra`, `docs`). Exemplo: `feat(backend): implementa autenticação JWT (BL-06)`.

Motivo: permite gerar changelog automaticamente (futuro) e comunica intenção da mudança sem abrir o diff.

### 1.3 Versionamento e Tags

- **Uma única linha de versão para o produto** (não por pasta), SemVer: `vMAJOR.MINOR.PATCH`.
  - `MAJOR`: mudança incompatível de schema de banco sem migração automática, ou de contrato de API pública.
  - `MINOR`: nova funcionalidade (novo tipo de relatório, novo endpoint).
  - `PATCH`: correção de bug, ajuste de template, dependência.
- Tag criada apenas em `main_back`/`main_front` (produção), após deploy bem-sucedido (ver Seção 4). Tag dispara o workflow `cd-production.yml` (Seção 3.3, hoje fallback manual — ver nota da DEC-17).
- `v0.x.y` enquanto o sistema não atingir os critérios de aceitação da v1.0 (`escopo.md`); `v1.0.0` = primeiro RFO completo gerado em produção fiel ao template do cliente.

### 1.4 Proteção das branches `main_front`/`main_back`/`staging_front`/`staging_back` (DEC-17)

Configurar em GitHub → Settings → Branches, uma regra por branch (ação manual do gestor do repositório, não automatizável por este plano — ver HT-05 em `backlog-tarefas-humanas.md`):

- Exigir Pull Request antes de merge (sem push direto, nem do próprio dono do repositório).
- Exigir que o workflow `ci.yml` passe (status check obrigatório) antes de permitir merge.
- Exigir branch atualizada com a branch-alvo antes do merge.
- Bloquear force-push e deleção das 4 branches.
- Squash merge como único método de merge habilitado (mantém histórico linear, 1 commit = 1 PR = 1 unidade de trabalho rastreável ao backlog).

### 1.5 Template de Pull Request

Criado em `.github/pull_request_template.md` (ver Seção 5) para garantir que todo PR referencie o item do backlog (`BL-XX`) e os requisitos (`RF/RN/RNF`) atendidos, e declare se há migração de banco ou variável de ambiente nova.

---

## 2. Ambientes

| Ambiente | Onde roda | Como é implantado | Dados |
|---|---|---|---|
| **Local (dev)** | Máquina do engenheiro/agente | `cd 05_infra && docker compose up -d` (`docker-compose.yml`) | Postgres/MinIO com dados de teste, sem backup |
| **Staging** | Render (`garra-backend-staging`/`garra-frontend-staging`, `render.yaml`) | Deploy automático nativo do Render a cada push em `staging_back`/`staging_front` (DEC-17) | Banco `garra-db-staging`, isolado do de produção; pode ser resetado a qualquer momento |
| **Produção** | Render (`garra-backend`/`garra-frontend`, `render.yaml`) | Deploy automático nativo do Render a cada push em `main_back`/`main_front` (`autoDeployTrigger: commit`) — SEM gate de aprovação manual por padrão; ver nota da DEC-17 se o gate for exigido | Banco `garra-db` — dados reais de clientes, sujeitos às políticas de backup (Seção 6) |

B-03 (hospedagem) foi resolvido em 2026-07-21 — Render escolhido (BL-20). `docker-compose.prod.yml`/`nginx.conf` (pensados para um VPS próprio) ficaram sem uso real; `cd-staging.yml`/`cd-production.yml` viraram fallback manual (`workflow_dispatch`) para esse cenário alternativo.

---

## 3. Pipelines de CI/CD (GitHub Actions)

Arquivos em `.github/workflows/`. Todos os workflows devem falhar rápido (lint/type-check antes de testes, testes antes de build de imagem).

### 3.1 `ci.yml` — Integração Contínua (todo PR e push em `main_front`/`main_back`/`staging_front`/`staging_back`, e ainda `main`/`staging` durante a transição)

1. **Lint + type-check**
   - Backend: `ruff check .` + `mypy app` (ou equivalente já configurado em `04_backend`).
   - Frontend: `next lint` + `tsc --noEmit` (`03_frontend`).
2. **Testes unitários**
   - Backend: `pytest` contra um Postgres de serviço (`services: postgres` do GitHub Actions), reaproveitando `04_backend/pytest.ini`/`conftest.py`.
   - Frontend: testes de componente (quando existirem — ainda não há suíte de testes de frontend no backlog atual; adicionar ao backlog quando a primeira tela com lógica não trivial for implementada).
3. **Build de imagens Docker** (cache de layers via `actions/cache` ou GitHub Actions cache do Buildx) para `04_backend/Dockerfile` e `03_frontend/Dockerfile`, sem push (apenas valida que o build funciona).
4. **Scan de vulnerabilidades**: Trivy (`aquasecurity/trivy-action`) nas imagens buildadas e `pip-audit`/`npm audit` nas dependências — falhas de severidade `HIGH`/`CRITICAL` bloqueiam o merge (BL-23 estende esta etapa com revisão manual OWASP).
5. **Testes E2E (BL-21)**: job `e2e` sobe a stack completa via `05_infra/docker-compose.yml` (Postgres, MinIO, backend, frontend), aplica migrations/seed do gabarito e roda os testes Playwright dos Fluxos RFO/LTIP (`03_frontend/e2e/*.spec.ts`) — ver "Testes E2E (Playwright, BL-21)" em `03_frontend/README.md`.

### 3.2 `cd-staging.yml` — Deploy em Staging (fallback manual, DEC-17)

- **Caminho real de deploy hoje**: nativo do Render — push em `staging_back`/`staging_front` já dispara `autoDeployTrigger: commit` nos serviços `garra-backend-staging`/`garra-frontend-staging` (`render.yaml`), sem passar por este workflow.
- Este workflow foi convertido para `workflow_dispatch` (só roda se disparado manualmente) e serve de fallback para um cenário de VPS próprio: build + push das imagens para o GitHub Container Registry (`ghcr.io`) com tag `staging-<sha curto>`; conexão via SSH (chave em secret) ao host de staging; `docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d`; roda migrations Alembic (`alembic upgrade head`) antes de subir o `backend`; healthcheck pós-deploy (`GET /health/ready`) com rollback automático se falhar (Seção 4.2).

### 3.3 `cd-production.yml` — Deploy em Produção (fallback manual, DEC-17)

- **Caminho real de deploy hoje**: nativo do Render — push em `main_back`/`main_front` já dispara `autoDeployTrigger: commit` nos serviços `garra-backend`/`garra-frontend`, **sem** o gate de aprovação manual abaixo. Se o gate (DEC-14) for obrigatório, ajustar `autoDeployTrigger` para `off` nesses serviços em `render.yaml` e usar este workflow (ou deploy manual via Dashboard/API do Render) como único caminho de publicação.
- Gatilho: criação de tag `v*.*.*` (mantém o esquema de versionamento independente do host).
- Exige **aprovação manual** via GitHub Environments (`production` environment com required reviewer = o próprio engenheiro/gestor).
- Mesmos passos do staging, porém: imagens com tag `<versão>` (não `latest`, para permitir rollback determinístico — Seção 4.2), backup pré-deploy do banco disparado antes da migration (Seção 6), e notificação (issue ou comentário automático) resumindo a versão implantada.

### 3.4 Secrets necessários (GitHub Actions → Settings → Secrets and variables)

| Secret | Uso |
|---|---|
| `SSH_HOST_STAGING` / `SSH_HOST_PROD` | Endereço do host de deploy |
| `SSH_PRIVATE_KEY` | Chave privada de deploy (usuário sem privilégio root, ver Seção 7) |
| `REGISTRY_USERNAME` / `GITHUB_TOKEN` | Push de imagens no GHCR (o `GITHUB_TOKEN` padrão do Actions já cobre GHCR) |
| `PROD_ENV_FILE` (ou secrets individuais) | Conteúdo do `.env` de produção, nunca commitado |

Nenhum secret é referenciado em `docker-compose.yml`/`docker-compose.prod.yml` diretamente — sempre injetado via `.env` gerado no runner a partir dos secrets no passo de deploy.

---

## 4. Estratégia de Deploy e Rollback

### 4.1 Deploy

- **Imutabilidade de imagem**: cada deploy usa uma tag de imagem específica (`staging-<sha>` ou `v1.2.3`), nunca `latest`, para que o host sempre saiba exatamente qual código está rodando e permitir reverter sem rebuild.
- **Migrations antes da aplicação subir**: `alembic upgrade head` roda como passo isolado do pipeline, antes de `docker compose up -d backend`, para nunca ter API nova apontando para schema antigo.
- **Zero-downtime simples**: `docker compose up -d` com `restart: unless-stopped` e healthcheck (já configurado em `05_infra/docker-compose.yml`) — para volume atual (uso individual/pequena equipe), não há necessidade de blue-green ou rolling update com load balancer; uma breve indisponibilidade (segundos) durante o restart do container é aceitável e deve ser comunicada como decisão explícita se isso mudar.

### 4.2 Rollback

- **Automático**: se o healthcheck pós-deploy (`GET /health/ready`) falhar dentro de um timeout definido (ex.: 60s), o workflow reexecuta `docker compose up -d` apontando para a tag de imagem anterior (guardada como output do job anterior) e marca o deploy como `falhou`.
- **Manual**: reverter é sempre possível via `docker compose -f docker-compose.prod.yml up -d` trocando a variável `IMAGE_TAG` no `.env` do host para a versão anterior — não depende do pipeline estar disponível.
- **Migrations de rollback**: toda migration Alembic nova deve ter um `downgrade()` funcional testado localmente antes do merge (checklist do PR, Seção 5) — mudanças de schema que não podem ser revertidas (ex.: drop de coluna com dados) exigem uma migration intermediária "additive" primeiro (expand/contract pattern), nunca destrutiva no mesmo deploy que a introduz.

---

## 5. Governança de Pull Request

Criar `.github/pull_request_template.md` com checklist mínimo:

```markdown
## O que este PR faz
<!-- descrição curta -->

## Referências
- Backlog: BL-XX
- Requisitos: RF-XX / RN-XX / RNF-XX

## Checklist
- [ ] Testes novos/atualizados e `pytest`/`next lint` passando localmente
- [ ] Sem segredo/credencial commitado (`.env`, chaves, tokens)
- [ ] Migration Alembic inclui `downgrade()` testado (se aplicável)
- [ ] Variáveis de ambiente novas documentadas em `.env.example`
- [ ] Documentação (`00_docs/`) atualizada, se o comportamento mudou
```

---

## 6. Backup e Disaster Recovery (coordenação com `05_infra`)

- Backup diário do volume `postgres_data` (dump lógico `pg_dump`, retenção 30 dias) — script a implementar em `05_infra/backup/backup-db.sh` (BL ainda não criada no backlog, ver Seção 8).
- Backup do bucket MinIO (fotos e PDFs/DOCX gerados) via `mc mirror` para um segundo destino (disco separado ou bucket remoto) — mesma retenção.
- Backup pré-deploy de produção: `cd-production.yml` dispara um dump avulso do banco antes de rodar `alembic upgrade head`, garantindo ponto de restauração imediatamente anterior a qualquer migration.
- Procedimento de restore documentado em `05_infra/backup/restore-db.sh` + seção correspondente em `05_infra/README.md` (a implementar).
- **[A ESCLARECER]** frequência/destino definitivo do backup fora do host de produção (RNF-08, lacuna já registrada em `arquitetura.md` Seção 11) — depende da decisão de hospedagem (B-03).

---

## 7. Segurança Operacional do Pipeline e do Host

- Deploy via SSH usa usuário dedicado sem privilégio `root` e sem acesso de `sudo` interativo; apenas os comandos `docker compose` necessários (via `sudo` restrito em `/etc/sudoers.d/`, se necessário).
- Firewall do host: apenas portas 80/443 (nginx) expostas publicamente; Postgres, Redis e MinIO acessíveis somente na rede interna do Docker Compose (já é o padrão em `docker-compose.yml` — bind em `127.0.0.1`).
- Certificados TLS via Let's Encrypt com renovação automática (`certbot` em container ou Caddy com TLS automático) — a definir na implementação de `nginx/nginx.conf` (BL-24).
- Scan de dependências (Trivy, `pip-audit`, `npm audit`) roda em todo PR (Seção 3.1) e semanalmente via workflow agendado (`schedule: cron`) para capturar CVEs publicados após o merge.
- Nenhum segredo em `docker-compose*.yml`, `Dockerfile` ou histórico do git — apenas em `.env` (local) ou GitHub Secrets (CI/CD), conforme já praticado em `05_infra/.env.example`.

---

## 8. Itens de Backlog Derivados deste Plano

Adicionar/ajustar em `backlog-tarefas.md` (Etapa 6/7):

| # | Tarefa | Depende de |
|---|---|---|
| BL-25 | Inicializar repositório Git local, primeiro commit e criação do repositório remoto no GitHub | Nenhuma — desbloqueada |
| BL-26 | Implementar `.github/workflows/ci.yml` (lint, testes, build, scan Trivy) | BL-25 |
| BL-27 | Implementar `docker-compose.prod.yml` + `nginx/nginx.conf` (HTTPS, reverse proxy) | BL-24 (já prevista) |
| BL-28 | Implementar `cd-staging.yml` e `cd-production.yml` (deploy via SSH + GHCR) | BL-26, BL-27, decisão de hospedagem (B-03) |
| BL-29 | Implementar `05_infra/backup/backup-db.sh` e `restore-db.sh` + agendamento (cron ou GitHub Actions schedule) | BL-27 |

---

## Referência de Decisão

Esta estratégia está registrada como **DEC-14** em [decisoes.md](decisoes.md#dec-14--gestão-de-configuração-github-trunk-based-conventional-commits-e-cicd-via-github-actions).
