# 04_backend

Aplicação **FastAPI (Python 3.12)** — API, regras de negócio, geração de relatórios (PDF/DOCX) e persistência.

> Modelo de dados implementado (BL-04): 14 entidades do diagrama ER (`00_docs/arquitetura.md` Seção 3) como modelos SQLAlchemy 2 (async), migration Alembic inicial e schemas Pydantic v2 básicos. Gabarito de sistemas prediais/subsistemas/tipos de anomalia/falha/localizações populado (BL-05) via seed idempotente a partir de `00_docs/convertidos/RFO_INSPECAO.md`, com endpoints de dados mestre em `GET /api/v1/sistemas-prediais` e `GET /api/v1/gabarito/*`. Autenticação e demais endpoints de domínio chegam nas tarefas seguintes do backlog (BL-06, BL-08...).

## Estrutura atual

```
04_backend/
├── app/
│   ├── api/v1/                # dados_mestre.py (sistemas-prediais, gabarito/*) — BL-05; demais endpoints de domínio em BL-06+
│   ├── models/                # 17 modelos SQLAlchemy 2 (async): 14 do ER (BL-04) + TipoAnomalia/TipoFalha/Localizacao (BL-05, DEC-13)
│   ├── schemas/                # schemas Pydantic v2 request/response (sem regras de negócio) — BL-04/BL-05
│   ├── scripts/                # rfo_gabarito_parser.py + seed_gabarito.py (BL-05, idempotente)
│   ├── services/               # regras de negócio (vazio — BL-06+)
│   ├── core/
│   │   ├── config.py            # Settings (Pydantic Settings) — Postgres, MinIO, JWT
│   │   └── database.py          # engine/sessão assíncrona SQLAlchemy 2
│   └── main.py                  # instância FastAPI, CORS, GET /health, router de dados mestre
├── templates/assets/            # logo, CSS compartilhado (vazio — BL-12+)
├── alembic.ini                  # config do Alembic (URL sobrescrita em runtime por env.py)
├── alembic/
│   ├── env.py                    # migrations async (asyncio.run + run_sync), target_metadata = app.models.Base.metadata
│   └── versions/                 # c22d4029c062_initial... (BL-04) + 8e2467ad6a92_gabarito_tipos... (BL-05)
├── tests/
│   ├── conftest.py               # fixture db_session (engine de teste com NullPool)
│   ├── test_health.py
│   ├── test_models.py            # testes de integração das 14 entidades e seus relacionamentos
│   └── test_gabarito.py          # parser + seed + endpoints de dados mestre (BL-05)
├── requirements.txt
├── Dockerfile
├── pytest.ini
├── conftest.py
└── .env.example
```

## Como rodar localmente (sem Docker)

```powershell
cd 04_backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env   # ajuste se necessário; padrão assume Postgres/MinIO publicados pelo docker-compose em 05_infra/
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`. Documentação OpenAPI automática em `http://localhost:8000/docs`.
Requer o PostgreSQL de [05_infra/docker-compose.yml](../05_infra/docker-compose.yml) rodando (`cd 05_infra && docker compose up -d postgres`) para que `GET /health` reporte `database: "ok"`.

## Como rodar via Docker Compose

```powershell
cd 05_infra
docker compose up -d --build backend
```

## Modelos de dados e migrations (BL-04)

```powershell
cd 05_infra
docker compose up -d postgres   # sobe o PostgreSQL publicado em localhost:5433

cd ..\04_backend
cp .env.example .env             # ajuste POSTGRES_PORT=5433 (porta publicada pelo docker-compose)
.venv\Scripts\Activate.ps1
alembic upgrade head             # aplica a migration inicial (14 tabelas)
alembic revision --autogenerate -m "descrição"   # gera novas migrations a partir dos modelos
```

A URL de conexão do Alembic vem de `Settings.database_url` (via `alembic/env.py`), não do `alembic.ini` — mesma fonte de verdade usada pela aplicação.

## Gabarito de sistemas prediais/subsistemas/tipos de anomalia/falha/localizações (BL-05)

Dados mestre (RF-10) extraídos de `00_docs/convertidos/RFO_INSPECAO.md` (parser em `app/scripts/rfo_gabarito_parser.py`, sem cópia manual dos valores — evita erro de transcrição) e persistidos via seed idempotente:

```powershell
cd 04_backend
alembic upgrade head              # cria as tabelas tipos_anomalia, tipos_falha, localizacoes (além das 14 do BL-04)
python -m app.scripts.seed_gabarito   # idempotente: pode ser rodado quantas vezes for preciso
```

Endpoints (somente leitura, dados mestre editados no futuro via CRUD de BL-14+):

| Endpoint | Descrição |
|---|---|
| `GET /api/v1/sistemas-prediais` | 15 sistemas prediais com seus subsistemas aninhados |
| `GET /api/v1/gabarito/tipos-anomalia` | 6 tipos de anomalia |
| `GET /api/v1/gabarito/tipos-falha` | 9 tipos de falha |
| `GET /api/v1/gabarito/localizacoes` | 47 localizações padrão |

Ver DEC-13 em [decisoes.md](../00_docs/projeto/decisoes.md) para a justificativa de `TipoAnomalia`/`TipoFalha`/`Localizacao` serem tabelas novas fora do diagrama ER original (o campo correspondente em `Ocorrencia` permanece texto livre até a BL-14+).

## Como rodar os testes

```powershell
cd 04_backend
pip install -r requirements.txt
pytest
```

Os testes de `tests/test_models.py` exigem o PostgreSQL do `05_infra/docker-compose.yml` rodando (usam `JSONB`, específico do dialeto PostgreSQL) e a migration aplicada. Cada teste remove os registros que cria.

## Referências

- Stack, modelo ER, contratos de API, padrões de projeto e system design: [00_docs/arquitetura.md](../00_docs/arquitetura.md) (Seções 9-11)
- Regras de negócio: [00_docs/estudo-do-contexto.md](../00_docs/estudo-do-contexto.md)
- Documentos/templates de origem: [01_output-context/](../01_output-context/)
- Prompt de scaffold: [.github/prompts/15-scaffold-backend-fastapi.prompt.md](../.github/prompts/15-scaffold-backend-fastapi.prompt.md)

## Convenção de execução (DEC-09)

Comandos Python/uvicorn/alembic deste app são executados a partir desta pasta (`04_backend/`). O `Dockerfile` de build/runtime também vive aqui; o `docker-compose.yml` que o referencia está em [05_infra/](../05_infra/) (build context `../04_backend`).

