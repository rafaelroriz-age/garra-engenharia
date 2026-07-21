# 05_infra

Infraestrutura, orquestração local e configuração de deploy do sistema.

## Decisão fixa (DEC-09 / ADR-05)

Sem aninhamento `src/`. Todo artefato de infraestrutura vive em `05_infra/` — nunca na raiz do repositório nem em `infra/` sem prefixo. `docker-compose.yml` e `.env.example` ficam em `05_infra/`; comandos Docker devem ser executados a partir dessa pasta (`cd 05_infra && docker compose up -d`). O build context dos serviços aponta para `../04_backend` e `../03_frontend`.

## Status atual (BL-01 — Fundação Técnica)

Implementado: `docker-compose.yml` com `postgres` (PostgreSQL 16) e `minio` (armazenamento S3-compatível), ambos com healthcheck e volume persistente, mais um job `createbuckets` que cria o bucket inicial. Serviços `backend`, `frontend`, `redis` e `celery-worker` ainda **não** estão neste arquivo — entram nos scaffolds BL-02/BL-03 (prompts 15/16) e na etapa de processamento assíncrono (DEC-10).

## Pré-requisitos

- Docker Desktop (ou Docker Engine + Compose plugin) instalado e em execução.
- Portas `5433`, `9000` e `9001` livres em `localhost` (o Postgres do container usa `5433` no host, e não `5432`, para não colidir com uma instalação nativa de PostgreSQL — ajuste `POSTGRES_PORT` no `.env` se necessário).

## Como rodar localmente

```powershell
cd 05_infra
Copy-Item .env.example .env   # ajuste as senhas antes de continuar
docker compose up -d
docker compose ps             # aguarde os dois serviços ficarem "healthy"
```

Acesso aos serviços após subir:

| Serviço | Endpoint | Credenciais |
|---|---|---|
| PostgreSQL | `localhost:5433` (banco `garra_engenharia`) | `POSTGRES_USER` / `POSTGRES_PASSWORD` do `.env` |
| MinIO API (S3) | `http://localhost:9000` | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` do `.env` |
| MinIO Console | `http://localhost:9001` | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` do `.env` |

O bucket definido em `MINIO_BUCKET_NAME` (padrão `relatorios-prediais`) é criado automaticamente pelo serviço `createbuckets` na primeira subida e permanece **privado** — o backend deve gerar URLs pré-assinadas com expiração para servir as fotos (ver DEC-02).

## Parar e reverter

```powershell
cd 05_infra
docker compose down       # para os containers, mantém os dados (volumes)
docker compose down -v    # para os containers e APAGA os dados (postgres_data, minio_data)
```

Não há migração de schema nesta etapa (BL-01 é somente infraestrutura), portanto não há passo de rollback de dados além de restaurar os volumes a partir de backup (ver `backup/`, a ser implementado em etapa futura).

## Conteúdo planejado (próximas etapas)

```
05_infra/
├── docker-compose.yml      # ✅ PostgreSQL + MinIO (dev) — implementado nesta etapa
├── docker-compose.prod.yml # Ambiente de produção
├── .env.example             # ✅ Todas as variáveis sem valores reais — implementado
├── .env.render.example       # ✅ Checklist de variáveis do deploy no Render
├── nginx/
│   └── nginx.conf           # Reverse proxy + HTTPS
├── backup/
│   ├── backup-db.sh
│   └── restore-db.sh
└── README.md                # Pré-requisitos, como rodar localmente, deploy e rollback
```

## Deploy em produção (Render)

Resolve o bloqueio B-03/HT-03 (hospedagem) com Render como provedor de nuvem. Toda a infraestrutura é definida como código em [`../render.yaml`](../render.yaml) (Render Blueprint) — os recursos abaixo são criados e conectados automaticamente, sem segredo hardcoded no repositório. Desde a DEC-17 (2026-07-21), cada serviço observa uma branch dedicada do monorepo (`main_front`/`main_back`/`staging_front`/`staging_back`) como gatilho de auto-deploy, em vez de todos dependerem de `main`:

| Serviço | Tipo Render | Origem | Branch |
|---|---|---|---|
| `garra-backend` | Web Service (Docker) | `04_backend/Dockerfile.render` | `main_back` |
| `garra-frontend` | Web Service (Docker) | `03_frontend/Dockerfile.render` | `main_front` |
| `garra-backend-staging` | Web Service (Docker) | `04_backend/Dockerfile.render` | `staging_back` |
| `garra-frontend-staging` | Web Service (Docker) | `03_frontend/Dockerfile.render` | `staging_front` |
| `garra-db` | PostgreSQL gerenciado (produção) | plano `basic-256mb` | — |
| `garra-db-staging` | PostgreSQL gerenciado (staging) | plano `basic-256mb` | — |

Os 2 serviços `-staging` e o banco `garra-db-staging` são recursos pagos adicionais — remova o bloco "Staging" de `render.yaml` antes de aplicar o Blueprint se ainda não quiser esse custo (ver comentário no topo do arquivo).

As imagens `Dockerfile.render` (uma por serviço) são versões de **produção** dos Dockerfiles de desenvolvimento — sem `--reload`/`next dev`, escutando na porta `$PORT` do Render, com build multi-stage no frontend (`output: "standalone"`). Os Dockerfiles de dev usados pelo `docker-compose.yml` local **não foram alterados**.

### Passo a passo (ação humana — requer conta Render + acesso ao GitHub do projeto)

1. Acesse [dashboard.render.com](https://dashboard.render.com/) → **New** → **Blueprint**.
2. Conecte o repositório GitHub `rafaelroriz-age/garra-engenharia`. Como cada serviço já declara sua própria `branch:` em `render.yaml` (`main_back`/`main_front`/`staging_back`/`staging_front`), a branch selecionada nesta tela serve apenas de branch padrão do Blueprint — não precisa coincidir com nenhuma delas.
3. O Render detecta `render.yaml` automaticamente e mostra um preview dos recursos (4 serviços web + 2 bancos, ou 2 serviços + 1 banco se o bloco de staging tiver sido removido). Nenhum campo pede preenchimento manual nesta versão (todos os segredos usam `generateValue`/`fromDatabase`).
4. Clique em **Apply**. O Render provisiona o banco primeiro, depois builda e sobe backend e frontend (a migration `alembic upgrade head` roda automaticamente via `preDeployCommand` antes de cada deploy do backend).
5. Ao final, cada serviço tem uma URL pública `https://<nome>.onrender.com` — confira em **Dashboard → serviço → Settings → URL**.

### Depois do 1º deploy — confirme os links reais

`render.yaml` assume que os hostnames ficam exatamente `garra-backend.onrender.com` e `garra-frontend.onrender.com`. Se o Render tiver atribuído um nome diferente (sufixo aleatório, caso o nome já estivesse em uso por outra conta):

1. Copie a URL real de cada serviço no Dashboard.
2. Atualize a env var `NEXT_PUBLIC_API_URL` do `garra-frontend` e `BACKEND_CORS_ORIGINS` do `garra-backend` com os valores corretos.
3. Dispare **Manual Deploy** nos dois serviços (o frontend precisa rebuildar, pois `NEXT_PUBLIC_API_URL` é embutida no bundle em build time).

Use [`.env.render.example`](.env.render.example) como checklist das variáveis de cada serviço.

### Limitações conhecidas desta primeira versão

- **Storage de fotos/documentos (MinIO/S3, DEC-02) não está incluído** — só os 3 serviços pedidos (frontend, backend, banco) foram provisionados. A API sobe e o `/health` funciona normalmente, mas os endpoints de upload de foto (BL-11) falham até alguém configurar `MINIO_*` manualmente no Dashboard apontando para um provedor S3-compatível externo (Cloudflare R2, AWS S3, Backblaze B2) ou provisionar um serviço `pserv` adicional rodando a imagem oficial do MinIO com disco persistente.
- Planos `starter` (web services) e `basic-256mb` (Postgres) são pagos (sem tier perpétuo gratuito) — confirme com o responsável pelo orçamento antes de aplicar o Blueprint, e ajuste `plan:` em `render.yaml` se preferir outro tier.
- HTTPS, health checks e deploy automático a cada `git push` na branch conectada já vêm prontos por padrão do Render (não precisa configurar Nginx/Let's Encrypt manualmente como em VPS próprio).

## Referências

- Stack e ADRs de infraestrutura: [00_docs/arquitetura.md](../00_docs/arquitetura.md)
- Decisão de estrutura de pastas: [00_docs/projeto/decisoes.md](../00_docs/projeto/decisoes.md) (DEC-09)
- Prompt de setup: [.github/prompts/14-setup-ambiente-desenvolvimento.prompt.md](../.github/prompts/14-setup-ambiente-desenvolvimento.prompt.md)
- Prompt de DevOps: [.github/prompts/12-devops.prompt.md](../.github/prompts/12-devops.prompt.md)

