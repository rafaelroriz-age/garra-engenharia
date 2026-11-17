# T87 · Neon como banco de produção, backend no PC (DEC-58)

Backend, túnel, `api.json`, snapshot e front no Pages seguem como na DEC-57. Só o PostgreSQL muda: em vez do
Postgres portátil do PC, o runtime local aponta para o **Neon** (conexão **direta**, sem `-pooler`, TLS).

## O que mudou

| Arquivo | Mudança |
|---|---|
| `04_backend/app/core/config.py` | O campo `postgres_ssl` **não existia** (o prompt supunha que sim): foi criado. `database_url` acrescenta `?ssl=require` (parâmetro do asyncpg) quando `POSTGRES_SSL=true`. Padrão `false`. |
| `04_backend/tests/test_config_postgres_ssl.py` | 5 testes: URL sem TLS (padrão), com TLS, `false` explícito, leitura de `POSTGRES_SSL` do ambiente, e confirmação de que `alembic/env.py` e `core/migrations.py` usam `get_settings().database_url` (mesma URL, herdam o TLS). |
| `05_infra/local/garra-local.ps1` | `POSTGRES_MODO=local\|neon` (padrão `local`, comportamento antigo intacto). Modo `neon`: ver abaixo. |
| `05_infra/local/.env.example`, `04_backend/.env.example` | Documentam `POSTGRES_MODO` e `POSTGRES_SSL`, com placeholders (sem valores reais). |

O agente (`garra-agente.ps1`, T82) não foi tocado: ele só lê o `.env` e chama o `garra-local.ps1`.

## Modo `POSTGRES_MODO=neon`

- `Get-Config` valida: host do Neon obrigatório (não `localhost`), **recusa host com `-pooler`** (asyncpg não funciona
  com o PgBouncer do pooler), exige senha, porta padrão 5432, `POSTGRES_SSL` assume `true` se vazio.
  Host, usuário e senha entram na lista de segredos do log (`Hide-Segredos`).
- `setup`: não baixa o Postgres portátil, não faz initdb nem cria banco; continua criando venv, Pango e `.env`.
  A senha do banco **não** é gerada aleatoriamente em cima da do Neon.
- `start`: testa a conexão ao Neon (`SELECT 1` + confere TLS ativo em `pg_stat_ssl`; log sem host/usuário/senha),
  roda `alembic upgrade head` contra o Neon, seeds idempotentes (a contagem do RAG usa Python/SQLAlchemy em vez de
  `psql`), sobe o uvicorn.
- `stop`: encerra só o uvicorn; não há banco local a parar.
- `status`: mostra `neon: conectado (neon-ok tls=True)` ou `SEM CONEXAO`.
- `backup`: no modo neon recusa com mensagem (backup do Neon é a T89; `pg_dump` precisa ser de versão compatível).

## O que rodou de verdade

- `ruff check .` em `04_backend`: verde.
- `pytest tests/test_config_postgres_ssl.py`: 5 passed.
- Suíte completa de `04_backend`: ver o item abaixo.
- Suíte completa (Postgres de dev em `localhost:5433`, 20 min): **485 passed, 65 failed, 229 errors, 14 skipped,
  7 xfailed**. Os 65 failed + 229 errors **não** vêm desta tarefa: a causa verificada em
  `test_vistoria_residencial_contexto.py` é `UndefinedColumnError: coluna "titulo_profissional" da relação
  "responsaveis" não existe`, isto é, o banco de dev está com o schema defasado (migrations não aplicadas), mais a
  falta da `libpango`. `test_auth.py` e `test_health.py` passam (9 passed). Para reproduzir limpo: `alembic upgrade
  head` no banco de dev antes do `pytest`. Não reexecutei depois disso.
- `garra-local.ps1`: parse sem erros e só ASCII. Com um `.env` descartável (apagado em seguida) e host fictício
  `.invalid`: host com `-pooler` → erro claro; `localhost` em modo neon → erro claro; `stop` em modo neon →
  "nada a parar no banco". Nenhuma conexão a Neon real.

## O que depende do dono (HT)

1. Criar o projeto no Neon (região próxima, ex.: São Paulo) e copiar a connection string **direta** (desligar o
   toggle "Pooled connection"; o host não deve ter `-pooler`).
2. No `05_infra/local/.env` (que está no `.gitignore`), preencher:
   ```
   POSTGRES_MODO=neon
   POSTGRES_HOST=<host direto do Neon>
   POSTGRES_PORT=5432
   POSTGRES_USER=<usuario>
   POSTGRES_PASSWORD=<senha>
   POSTGRES_DB=<banco>
   POSTGRES_SSL=true
   ```
3. Rodar `garra-local.ps1 setup`, depois `start`, depois `status` e conferir `neon: conectado (neon-ok tls=True)`.
   O primeiro `start` aplica todas as migrations no banco vazio do Neon e roda os seeds.
4. Migrar os dados do Render para o Neon é a T88; backup/documentação, a T89.

Observação: o Neon escala a zero; a primeira conexão após ociosidade pode levar alguns segundos. Se o `start`
falhar por isso, rodar de novo.

## Decisão proposta (para o fechamento de lote)

DEC-58: o banco de produção é o Neon (grátis, não expira, escala a zero), com o backend no PC do dono; ajusta a
P1 da DEC-57 (Postgres portátil continua suportado como `POSTGRES_MODO=local`).
