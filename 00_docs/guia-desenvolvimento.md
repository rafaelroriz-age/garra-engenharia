---
title: Guia de desenvolvimento — instalar, rodar e testar
type: knowledge
status: draft
owner: Garra Engenharia
related:
  - 05_infra/README.md
  - 04_backend/README.md
  - 03_frontend/README.md
  - 00_docs/configuracao.md
tags: [setup, desenvolvimento, testes, docker, onboarding]
last_updated: 2026-11-03
---

<!-- ai-summary
System: roteiro único para subir o ambiente local e rodar os testes do monorepo.
Flow: 05_infra (.env + docker compose) -> 04_backend (.env com porta 5433, alembic, seeds, uvicorn) -> 03_frontend (npm) -> testes.
Owner: Garra Engenharia.
Status: draft — escrito na D04 (2026-11-03) a partir dos READMEs de pasta e do código; a sequência não foi executada de ponta a ponta nesta tarefa (sem Docker no PATH).
-->

# Guia de desenvolvimento

Sequência completa para levantar o sistema na máquina local e rodar os testes. Os detalhes de cada parte continuam nos READMEs de pasta: [05_infra](../05_infra/README.md), [04_backend](../04_backend/README.md) e [03_frontend](../03_frontend/README.md). As variáveis de ambiente estão em [configuracao.md](configuracao.md).

> Convenção do monorepo (DEC-09): comandos Python, `pytest` e `alembic` rodam a partir de `04_backend/`; `npm` a partir de `03_frontend/`; `docker compose` a partir de `05_infra/`.

## 1. Pré-requisitos

| Ferramenta | Versão de referência | Onde está fixada |
|---|---|---|
| Docker + Docker Compose | não fixada | `05_infra/docker-compose.yml` |
| Python | 3.12 | `04_backend/Dockerfile` (`FROM python:3.12-slim`), `.github/workflows/ci.yml` (`python-version: "3.12"`) |
| Node.js | 20 | `03_frontend/Dockerfile` (`FROM node:20-alpine`), `ci.yml` (`node-version: "20"`) |

Versões usadas na última execução registrada (D01, 2026-10-28): Python 3.12.4, Node v26.7.0, npm 11.19.0, ruff 0.15.1 (`00_docs/_preparo/01_sistema.md` §5.2).

## 2. Subir a infraestrutura (PostgreSQL e MinIO)

```powershell
cd 05_infra
Copy-Item .env.example .env        # troque as senhas; o compose exige POSTGRES_PASSWORD, MINIO_ROOT_* e JWT_SECRET_KEY
docker compose up -d postgres minio createbuckets
docker compose ps                  # aguarde "healthy"
```

- O PostgreSQL fica em `127.0.0.1:5433` e o MinIO em `9000` (API) e `9001` (console) (`05_infra/docker-compose.yml:54`, `:76`, `:78`).
- `createbuckets` cria o bucket `MINIO_BUCKET_NAME` (padrão `relatorios-prediais`) (`docker-compose.yml:90-106`).
- Para subir também `backend` (porta 8000) e `frontend` (porta 3000) em container: `docker compose up -d --build` (`docker-compose.yml:111`, `:150`). Nesse modo, o `04_backend/.env` não é usado: o compose injeta as variáveis (`04_backend/.env.example`, cabeçalho).

## 3. Backend (FastAPI)

```powershell
cd 04_backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env        # depois edite: POSTGRES_PORT=5433
alembic upgrade head               # 6 migrations em alembic/versions/
python -m app.scripts.seed_gabarito   # sistemas, subsistemas, tipos de anomalia/falha, localizações (idempotente)
$env:ADMIN_SENHA = "<senha forte>"; python -m app.scripts.seed_admin   # primeiro usuário auditor
uvicorn app.main:app --reload      # http://localhost:8000
```

- **Porta 5433, não 5432.** `04_backend/.env.example` traz `POSTGRES_PORT=5432` e o padrão de `Settings` também é 5432 (`app/core/config.py:33`), mas o compose publica 5433. Sem o ajuste, o backend e os testes conectam em outro PostgreSQL, se houver um na 5432 (aconteceu na D01: serviço Windows `postgresql-x64-17`, `01_sistema.md` §5.2).
- `seed_admin` lê `ADMIN_EMAIL`, `ADMIN_SENHA` e `ADMIN_NOME`; sem `ADMIN_SENHA`, usa uma senha padrão embutida (`app/scripts/seed_admin.py:56-58`). Defina a variável.
- Healthcheck: `GET /health` (`app/main.py`). A documentação interativa (`/docs`) só é exposta com `ENVIRONMENT` de desenvolvimento (`app/main.py`; valores aceitos em `app/core/config.py:68`).
- **PDF no Windows:** o WeasyPrint precisa das bibliotecas GTK, que não existem no venv local do Windows; o PDF só renderiza dentro do container do backend (`04_backend/README.md`, seção BL-12/BL-13).
- Geração de relatório: não há rota na API (`grep` em `app/api/v1/` sem rota de relatório). O PDF/DOCX do RFO só sai por script (`app/scripts/benchmark_relatorio_geracao.py`), ver [arquitetura.md](arquitetura.md) "Estado da implementação".

## 4. Frontend (Next.js)

```powershell
cd 03_frontend
npm install
npm run dev                        # http://localhost:3000
```

A URL da API vem de `NEXT_PUBLIC_API_URL`, com padrão `http://localhost:8000/api/v1` (`03_frontend/lib/api-client.ts:14`). Não existe `03_frontend/.env.example` (`ls -a 03_frontend`); a variável está em `05_infra/.env.example` para o modo Docker.

## 5. Testes

| Parte | Comando (na pasta) | Pré-condição | Fonte |
|---|---|---|---|
| Backend | `pytest` (`04_backend/`) | PostgreSQL e MinIO no ar, `.env` com `POSTGRES_PORT=5433`, `alembic upgrade head` aplicado | `pytest.ini`; `tests/conftest.py` usa `get_settings().database_url`; `01_sistema.md` §5.2 |
| Backend (lint) | `ruff check .` (`04_backend/`) | `pip install ruff` (não está em `requirements.txt`) | `.github/workflows/ci.yml:77` |
| Frontend (lint) | `npm run lint` (`03_frontend/`) | `npm install` | `package.json` (`"lint": "next lint"`) |
| Frontend (build) | `npm run build` (`03_frontend/`) | `npm install` | `package.json` |
| E2E | `npm run test:e2e` (`03_frontend/`) | stack completa no ar (`docker compose up -d --build`), migrations, `seed_gabarito` e o admin de bootstrap; `npx playwright install --with-deps chromium` uma vez | `playwright.config.ts`; `03_frontend/README.md` "Testes E2E"; `ci.yml`, job `e2e` |

Observações verificadas:

- O `ruff` procura configuração nas pastas acima de `04_backend/`. Não há `pyproject.toml` nem `ruff.toml` no repositório; na D01, um `pyproject.toml` fora do repositório mudou o resultado de 47 para 201 erros (`01_sistema.md` §5.2). Para reproduzir o CI, use `ruff check . --isolated`.
- No CI o lint do backend não bloqueia (`continue-on-error: true`, `ci.yml:81-83`), e o lint do frontend também não (`continue-on-error: true` no passo "Lint (next lint)").
- O job `backend` do `ci.yml` roda `pytest --maxfail=1` sem `alembic upgrade head` antes. Se os testes que dependem de tabela passam no Actions assim: **não determinado** (os logs do Actions não foram consultados).
- Os testes E2E usam `E2E_ADMIN_EMAIL`/`E2E_ADMIN_SENHA` para logar com o admin de bootstrap (`03_frontend/e2e/helpers.ts:65-66`); os padrões batem com os de `seed_admin.py`.

## 6. Problemas conhecidos

| Sintoma | Causa | Correção |
|---|---|---|
| `UndefinedTableError` ou conexão recusada nos testes | backend apontando para a 5432 | `POSTGRES_PORT=5433` no `04_backend/.env` |
| `EndpointConnectionError` em `test_storage.py` | MinIO fora do ar | `docker compose up -d minio createbuckets` |
| `ModuleNotFoundError: openpyxl` / `pdfplumber` na coleta | venv sem `requirements.txt` completo | `pip install -r requirements.txt` |
| Erro do WeasyPrint (GTK) | Windows sem GTK | gerar o PDF dentro do container do backend |
| Backend não sobe com `ENVIRONMENT=production` | `JWT_SECRET_KEY` padrão ou com menos de 32 caracteres, ou CORS `*` (fail-closed) | `app/core/config.py:71-81` |

## Registro

- Escrito na D04 (2026-11-03). Nenhum comando desta página foi executado de ponta a ponta nesta tarefa: o Docker não está no PATH e as portas 5433 e 9000 estavam fechadas (`Test-NetConnection`). A conferência dos comandos é a D05.
