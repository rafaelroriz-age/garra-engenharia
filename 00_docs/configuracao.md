---
title: Referência de configuração — variáveis de ambiente
type: knowledge
status: ativo
owner: Garra Engenharia
related:
  - 04_backend/app/core/config.py
  - 04_backend/.env.example
  - 05_infra/.env.example
  - 05_infra/.env.render.example
  - render.yaml
  - 00_docs/guia-desenvolvimento.md
tags: [configuracao, env, deploy, render, docker]
last_updated: 2026-11-03
---

<!-- ai-summary
System: tabela única das variáveis de ambiente do backend, do frontend, do compose e dos testes E2E.
Flow: Settings (pydantic-settings, 04_backend/app/core/config.py) lê o ambiente ou 04_backend/.env; o compose (05_infra/.env) e o Render (render.yaml) injetam as variáveis.
Owner: Garra Engenharia.
Status: ativo (verificado na D05, 2026-11-04) — levantado do código na D04 (2026-11-03).
-->

# Referência de configuração

O backend lê a configuração pela classe `Settings` (`04_backend/app/core/config.py`), com `pydantic-settings`: os nomes não diferenciam maiúsculas e minúsculas, o arquivo `.env` é lido da pasta de execução (`env_file=".env"`) e variáveis desconhecidas são ignoradas (`extra="ignore"`).

**Onde cada variável é definida**

| Sigla | Arquivo | Uso |
|---|---|---|
| **B** | `04_backend/.env.example` | backend fora do Docker (copiar para `04_backend/.env`) |
| **I** | `05_infra/.env.example` | `docker compose` local (copiar para `05_infra/.env`) |
| **R** | `render.yaml` | Blueprint de produção no Render |
| **RE** | `05_infra/.env.render.example` | checklist das variáveis do Render; não é lido por nenhum processo (cabeçalho do arquivo) |

## 1. Backend (`Settings`)

| Variável | Padrão em `Settings` | Definida em | Obrigatória fora de dev | Efeito |
|---|---|---|---|---|
| `ENVIRONMENT` | `development` | B, R (`production`), RE | — | `development`, `dev`, `local` e `test` contam como desenvolvimento (`config.py:68`). Fora deles: ativa o fail-closed, HSTS e esconde `/docs`, `/redoc` e `/openapi.json` (`app/main.py:48-59`) |
| `APP_NAME` | `Sistema de Automação de Relatórios Prediais` | nenhum | não | nome da aplicação |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000` | B, I, R, RE | sim: não pode conter `*` (`config.py:79-80`) | origens CORS, separadas por vírgula |
| `RUN_MIGRATIONS_ON_STARTUP` | `False` | R (`"false"`); **ausente de B, I e RE** | não | se `true`, roda `alembic upgrade head` no boot (`app/main.py:41-42`, `app/core/migrations.py`). O comentário em `render.yaml` diz que o serviço `garra-backend` realmente provisionado usa runtime nativo, sem `preDeployCommand`, e precisa desta variável como `true` |
| `POSTGRES_USER` | `garra` | B, I, R (`fromDatabase`) | — | usuário do banco |
| `POSTGRES_PASSWORD` | vazio | B, I, R (`fromDatabase`) | — | senha; o compose exige (`docker-compose.yml:48`, `:?`) |
| `POSTGRES_DB` | `garra_engenharia` | B, I, R (`fromDatabase`) | — | nome do banco |
| `POSTGRES_HOST` | `localhost` | B, R (`fromDatabase`); o compose fixa `postgres` (`docker-compose.yml:124`) | — | host do banco |
| `POSTGRES_PORT` | `5432` | B (**5432**), I (**5433**), R (`fromDatabase`); o compose fixa 5432 dentro da rede (`docker-compose.yml:125`) | — | porta. Fora do Docker use **5433**, a porta publicada pelo compose (`docker-compose.yml:54`); ver [guia-desenvolvimento.md](guia-desenvolvimento.md) |
| `MINIO_ROOT_USER` | vazio | B, I; comentada em R | — | credencial S3; o compose exige (`docker-compose.yml:72`) |
| `MINIO_ROOT_PASSWORD` | vazio | B, I; comentada em R | — | idem |
| `MINIO_BUCKET_NAME` | `relatorios-prediais` | B, I, RE; comentada em R | — | bucket de fotos e arquivos |
| `MINIO_HOST` | `localhost` | B; o compose fixa `minio` (`docker-compose.yml:129`); comentada em R | — | host S3 |
| `MINIO_API_PORT` | `9000` | B, I | — | porta S3 |
| `MINIO_USE_SSL` | `False` | B; comentada em R | — | `https` no endpoint S3 (`config.py`, `minio_endpoint_url`) |
| `JWT_SECRET_KEY` | `changeme` | B, I, R (`generateValue: true`) | sim: não pode ser vazia, `changeme` ou ter menos de 32 caracteres (`config.py:73-78`) | assinatura dos tokens |
| `JWT_ALGORITHM` | `HS256` | B, I, R | — | algoritmo do JWT |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | B, I, R | — | validade do token |

**Storage em produção:** as variáveis `MINIO_*` estão comentadas no `render.yaml` ("FICOU FORA do escopo deste Blueprint") e vazias no `.env.render.example`. Sem elas, os padrões de `Settings` apontam para `localhost:9000` sem credenciais. O próprio `render.yaml` avisa que os endpoints de upload e foto falham nesse caso. Se a produção atual tem storage configurado no Dashboard: **não determinado**.

## 2. Scripts do backend

| Variável | Padrão | Lida por | Efeito |
|---|---|---|---|
| `ADMIN_EMAIL` | `admin@garra-engenharia.com.br` | `app/scripts/seed_admin.py:56` | e-mail do auditor de bootstrap |
| `ADMIN_SENHA` | senha padrão embutida | `seed_admin.py:57` | senha do auditor de bootstrap. Defina sempre: o padrão é conhecido (está no código e nos testes E2E) |
| `ADMIN_NOME` | `Administrador` | `seed_admin.py:58` | nome do usuário |

## 3. Docker Compose (`05_infra/.env`)

Além das variáveis do backend, o `05_infra/.env.example` define:

| Variável | Valor de exemplo | Efeito |
|---|---|---|
| `POSTGRES_PORT` | `5433` | porta publicada em `127.0.0.1` |
| `MINIO_CONSOLE_PORT` | `9001` | console web do MinIO |
| `BACKEND_PORT` | `8000` | porta publicada do backend |
| `FRONTEND_PORT` | `3000` | porta publicada do frontend |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | repassada ao serviço `frontend` (`docker-compose.yml:157`) |

## 4. Frontend

| Variável | Padrão no código | Definida em | Efeito |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` (`03_frontend/lib/api-client.ts:14`) | I, R, RE; **não há `03_frontend/.env.example`** | base da API. É embutida no bundle no build: mudar exige novo build/deploy (`05_infra/.env.render.example`, seção `garra-frontend`; `render.yaml`, comentário do `garra-frontend`) |

## 5. Testes E2E (Playwright)

| Variável | Padrão | Lida por |
|---|---|---|
| `E2E_BASE_URL` | `http://localhost:3000` | `03_frontend/playwright.config.ts:22` |
| `E2E_API_BASE_URL` | `http://localhost:8000/api/v1` | `03_frontend/e2e/helpers.ts:9` |
| `E2E_ADMIN_EMAIL` | igual ao padrão de `ADMIN_EMAIL` | `e2e/helpers.ts:65` |
| `E2E_ADMIN_SENHA` | igual ao padrão de `ADMIN_SENHA` | `e2e/helpers.ts:66` |
| `CI` | — | `playwright.config.ts:16-19` (`forbidOnly`, `retries`, `reporter`) |

## 6. CI (`.github/workflows/ci.yml`)

O job `backend` define `ENVIRONMENT=test`, `POSTGRES_*` apontando para o serviço `postgres` do Actions em `localhost:5432` e um `JWT_SECRET_KEY` só de CI. Os secrets de deploy por SSH/GHCR estão listados em [plano-gestao-configuracao.md](projeto/plano-gestao-configuracao.md) §3.4.

## Divergências registradas (decisão no fechamento de lote)

São arquivos de configuração, fora do escopo de uma tarefa de documentação. As propostas P-01 a P-03 estão em `00_docs/_preparo/01_sistema.md` §7.

1. `RUN_MIGRATIONS_ON_STARTUP` não está em nenhum `.env.example`.
2. `04_backend/.env.example` usa `POSTGRES_PORT=5432`; o compose publica 5433 (P-01).
3. Não há `03_frontend/.env.example`; `NEXT_PUBLIC_API_URL` só aparece no `05_infra/.env.example` e no Render.
4. `render.yaml` sem `MINIO_*` para o backend (P-03).
