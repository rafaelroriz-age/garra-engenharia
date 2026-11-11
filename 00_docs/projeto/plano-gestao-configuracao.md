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
last_updated: 2026-11-03
---

> **Revisão de 2026-11-03 (D04):** §1.1, §1.4, §2, §3.1 e §3.2 foram reescritas para refletir a DEC-22 (remoção do staging e sincronização automática `main` → `main_back`/`main_front`) e o que `.github/workflows/ci.yml` roda de fato. As demais seções não mudaram.

# Plano de Gestão de Configuração (Git, CI/CD, Deploy)

> Define como o código é versionado, integrado, empacotado e implantado. Complementa `00_docs/arquitetura.md` (stack e ADRs) e `05_infra/README.md` (execução local). Referência de governança de decisões: `decisoes.md` DEC-14.

## 1. Estrutura de Repositório

**Modelo:** monorepo único no GitHub (`garra-engenharia`), contendo `00_docs/` a `05_infra/` e `.github/`. Justificativa: equipe pequena (1 engenheiro + agentes), forte acoplamento entre frontend/backend/infra nesta fase, e histórico único facilita rastrear uma feature ponta-a-ponta (fatia vertical, conforme `ciclo-de-vida.md`).

Não versionar: `.env`, `.env.*` (exceto `.env.example`), `node_modules/`, `.next/`, `.venv/`, `__pycache__/`, volumes Docker — já cobertos pelo `.gitignore` existente na raiz.

### 1.1 Branching — Trunk-Based com tronco `main` e 2 branches de deploy (DEC-17, simplificado pela DEC-22)

- **`main` é o tronco único**: todo commit e todo PR, inclusive do Dependabot, é integrado em `main` (`.github/workflows/ci.yml`, cabeçalho; `render.yaml`, cabeçalho).
- 2 branches de deploy, cada uma gatilho de UM serviço no Render (o conteúdo do monorepo é o mesmo nas duas — sem histórico filtrado, sem quebrar DEC-09):
  - `main_back` — produção do backend (`garra-backend` em `render.yaml`)
  - `main_front` — produção do frontend (`garra-frontend`)
- `main_back` e `main_front` recebem `main` **automaticamente**, por merge (não force-push), a cada push em `main` (`.github/workflows/sync-deploy-branches.yml`). Não se commita direto nelas nem se abre PR contra elas. Se o merge automático der conflito, o workflow abre uma issue.
- Staging (`staging_back`, `staging_front`, `staging`) foi **removido** em 2026-08-05 (DEC-22): nunca chegou a ser provisionado no Render (HT-04). `git branch -r` não lista nenhuma branch de staging.
- Branches de trabalho de vida curta (idealmente < 3 dias), a partir de `main`:
  - `feat/<slug>` — nova funcionalidade (ex.: `feat/bl-06-auth-jwt`)
  - `fix/<slug>` — correção de bug
  - `chore/<slug>` — infra, dependências, configuração
  - `docs/<slug>` — apenas documentação (`00_docs/`)
- Uma mudança que afeta front e back vai num único PR para `main`; a sincronização leva o mesmo conteúdo às duas branches de deploy.
- Sem `develop`/`release/*` — o backlog (`backlog-tarefas.md`) já cumpre o papel de plano de releases; branches longas de release adicionariam overhead desproporcional ao porte da equipe (mesmo racional de DEC-08).
- Rebase (não merge commit) da branch de feature sobre `main` antes de abrir PR, para manter histórico linear; merge do PR via **squash merge** (1 commit por PR).

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

### 1.4 Proteção das branches `main`, `main_back` e `main_front` (DEC-17, DEC-22)

Configurar em GitHub → Settings → Branches (ação manual do gestor do repositório, não automatizável por este plano — ver HT-05 em `backlog-tarefas-humanas.md`). Se as regras já estão configuradas no GitHub: **não determinado** (não consultado).

- **`main`**: exigir Pull Request antes de merge; exigir que o workflow `ci.yml` passe (é o status check obrigatório para merge em `main`, segundo o cabeçalho do `ci.yml`); exigir branch atualizada antes do merge; squash merge como único método (1 commit = 1 PR = 1 unidade de trabalho rastreável ao backlog).
- **`main_back` e `main_front`**: bloquear force-push e deleção. O push nelas vem do `sync-deploy-branches.yml` (com `permissions: contents: write`), então a regra precisa permitir esse push do `github-actions[bot]`.

### 1.5 Template de Pull Request

Criado em `.github/pull_request_template.md` (ver Seção 5) para garantir que todo PR referencie o item do backlog (`BL-XX`) e os requisitos (`RF/RN/RNF`) atendidos, e declare se há migração de banco ou variável de ambiente nova.

---

## 2. Ambientes

| Ambiente | Onde roda | Como é implantado | Dados |
|---|---|---|---|
| **Local (dev)** | Máquina do engenheiro/agente | `cd 05_infra && docker compose up -d` (`docker-compose.yml`) | Postgres/MinIO com dados de teste, sem backup |
| **Produção** | Render (`garra-backend`/`garra-frontend`, `render.yaml`) | Deploy automático nativo do Render a cada push em `main_back`/`main_front` (`autoDeployTrigger: commit`), que recebem `main` pelo `sync-deploy-branches.yml` — SEM gate de aprovação manual por padrão; ver nota da DEC-17 se o gate for exigido. O `garra-backend` do Blueprint roda `preDeployCommand: alembic upgrade head`; o serviço realmente provisionado usa runtime nativo e depende de `RUN_MIGRATIONS_ON_STARTUP=true` (comentário em `render.yaml`) | Banco `garra-db` — dados reais de clientes, sujeitos às políticas de backup (Seção 6) |

Não há ambiente de staging (DEC-22).

B-03 (hospedagem) foi resolvido em 2026-07-21 — Render escolhido (BL-20). `docker-compose.prod.yml`/`nginx.conf` (pensados para um VPS próprio) ficaram sem uso real; `cd-staging.yml`/`cd-production.yml` viraram fallback manual (`workflow_dispatch`) para esse cenário alternativo.

---

## 3. Pipelines de CI/CD (GitHub Actions)

Arquivos em `.github/workflows/`. Todos os workflows devem falhar rápido (lint/type-check antes de testes, testes antes de build de imagem).

### 3.1 `ci.yml` — Integração Contínua (todo PR para `main` e push em `main`, `main_back` e `main_front`)

Gatilhos: `pull_request` para `main`; `push` em `main_front`, `main_back` e `main` (`ci.yml`, bloco `on:`). Execuções antigas da mesma branch são canceladas (`concurrency`). Jobs, como estão no arquivo:

1. **`backend`** (`04_backend`, Python 3.12, serviço `postgres:16-alpine` do Actions na porta 5432, `ENVIRONMENT=test`):
   - `pip install -r requirements.txt` e `pip install ruff` (o `ruff` não está em `requirements.txt`);
   - `ruff check .` com `continue-on-error: true` — **não bloqueia** o merge (comentário no arquivo: "Lint ainda não é bloqueante");
   - `pytest --maxfail=1`. O job não roda `alembic upgrade head` antes; se os testes que dependem de tabela passam assim no Actions: **não determinado** (logs não consultados).
   - Não há `mypy` nem outro type-check no backend.
2. **`frontend`** (`03_frontend`, Node 20): `npm ci`; `npm run lint` com `continue-on-error: true` (não bloqueante); `npm run build`. Não há `tsc --noEmit` separado nem testes de componente.
3. **`docker-build-scan`** (depois de `backend` e `frontend`): build das imagens sem push e scan Trivy (`aquasecurity/trivy-action`) com `severity: HIGH,CRITICAL` e `exit-code: "1"` (bloqueia). Não há `pip-audit` nem `npm audit` no workflow (`grep -n "pip-audit\|npm audit" .github/workflows/ci.yml` → vazio).
4. **`e2e`** (BL-21, depois de `backend` e `frontend`): sobe `05_infra/docker-compose.yml`, roda `alembic upgrade head`, `seed_gabarito` e `seed_admin` dentro do container `backend`, instala o Chromium do Playwright e roda `npx playwright test` (Fluxos RFO/LTIP, `03_frontend/e2e/*.spec.ts`); publica o relatório em caso de falha e derruba a stack no fim — ver "Testes E2E (Playwright, BL-21)" em `03_frontend/README.md`.

### 3.2 `cd-staging.yml` — VPS própria (fallback manual)

- **Não há staging no Render** (DEC-22). O nome do arquivo é herança da DEC-17.
- O workflow só roda por `workflow_dispatch` (disparo manual, `cd-staging.yml`, bloco `on:`) e serve de fallback para um cenário de VPS própria: build + push das imagens para o GitHub Container Registry (`ghcr.io`) com tag `staging-<sha>` (`github.sha` completo); conexão via SSH (chave em secret) ao host; `docker compose -f docker-compose.prod.yml pull`, `run --rm backend alembic upgrade head` e `up -d`; healthcheck pós-deploy com `curl` em `http://localhost:8000/health/ready`.
- **Divergência com o código:** o backend só expõe `GET /health` (`app/main.py`); `GET /health/ready` não existe, então o passo de healthcheck desse workflow falharia. O workflow também não tem passo de rollback automático (o arquivo termina no healthcheck): o rollback da Seção 4.2 não está implementado nele.

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

- Backup diário do volume `postgres_data` (dump lógico `pg_dump`, retenção 30 dias) — script em `05_infra/backup/backup-db.sh` (BL-29; uso descrito em `05_infra/README.md`, "Backup e restauração").
- Backup do bucket MinIO (fotos e PDFs/DOCX gerados) via `mc mirror` para um segundo destino (disco separado ou bucket remoto) — mesma retenção.
- Backup pré-deploy de produção: `cd-production.yml` dispara um dump avulso do banco antes de rodar `alembic upgrade head`, garantindo ponto de restauração imediatamente anterior a qualquer migration.
- Procedimento de restore em `05_infra/backup/restore-db.sh` + seção "Backup e restauração (BL-29, RNF-08)" em `05_infra/README.md`.
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
