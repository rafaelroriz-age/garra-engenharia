# 05_infra

Infraestrutura, orquestração local e configuração de deploy do sistema.

## Decisão fixa (DEC-09 / ADR-05)

Sem aninhamento `src/`. Todo artefato de infraestrutura vive em `05_infra/` — nunca na raiz do repositório nem em `infra/` sem prefixo. `docker-compose.yml` e `.env.example` ficam em `05_infra/`; comandos Docker devem ser executados a partir dessa pasta (`cd 05_infra && docker compose up -d`). O build context dos serviços aponta para `../04_backend` e `../03_frontend`.

## Status atual (BL-01 — Fundação Técnica)

Implementado: `docker-compose.yml` com `postgres` (PostgreSQL 16) e `minio` (armazenamento S3-compatível), ambos com healthcheck e volume persistente, mais um job `createbuckets` que cria o bucket inicial. Serviços `backend`, `frontend`, `redis` e `celery-worker` ainda **não** estão neste arquivo — entram nos scaffolds BL-02/BL-03 (prompts 15/16) e na etapa de processamento assíncrono (DEC-10).

## Pré-requisitos

- Docker Desktop (ou Docker Engine + Compose plugin) instalado e em execução. (O diagnóstico T01 de 2026-11-04 achou a máquina de desenvolvimento sem Docker, com as portas 5433 e 9000 fechadas — ver [diagnostico.md](../00_docs/backlog-auto/diagnostico.md).)
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
├── docker-compose.yml      # ✅ PostgreSQL + MinIO + backend + frontend (dev)
├── docker-compose.prod.yml # ✅ Stack de produção em VPS próprio (BL-27)
├── .env.example             # ✅ Todas as variáveis sem valores reais — implementado
├── .env.render.example       # ✅ Checklist de variáveis do deploy no Render
├── nginx/
│   └── nginx.conf           # ✅ Reverse proxy + HTTPS (BL-27)
├── backup/
│   ├── backup-db.sh         # ✅ Dump do Postgres + espelho do MinIO (BL-29)
│   └── restore-db.sh        # ✅ Restore com confirmação e dump prévio (BL-29)
└── README.md                # Pré-requisitos, como rodar localmente, deploy e rollback
```

## Deploy em VPS próprio (alternativa ao Render — BL-27)

A hospedagem oficial é o Render (seção abaixo). `docker-compose.prod.yml` + `nginx/nginx.conf` cobrem o cenário alternativo de VPS próprio previsto em DEC-14/DEC-17 e consumido pelos workflows de fallback `cd-staging.yml`/`cd-production.yml`.

Diferenças em relação ao compose de desenvolvimento:

- Usa **imagens prontas do GHCR** com tag imutável (`IMAGE_TAG`), nunca `build:` nem `latest` — permite rollback determinístico.
- **Nenhuma porta de Postgres/MinIO/backend/frontend é publicada** no host: só o Nginx expõe 80/443.
- Nginx faz TLS termination (Let's Encrypt via `certbot`, renovação automática), rate limiting em `/api/v1/auth/login` (OWASP A07) e cabeçalhos de segurança (HSTS, `X-Frame-Options`, `nosniff`).

```bash
cd 05_infra
cp .env.example .env                 # preencher com os segredos reais
export IMAGE_TAG=v1.0.0              # ou staging-<sha>
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
docker compose -f docker-compose.prod.yml up -d
```

Antes do primeiro `up`, substitua `SEU.DOMINIO` em `nginx/nginx.conf` e emita o certificado inicial:

```bash
docker compose -f docker-compose.prod.yml run --rm --entrypoint \
  "certbot certonly --webroot -w /var/www/certbot -d SEU.DOMINIO --email SEU@EMAIL --agree-tos --no-eff-email" certbot
```

**Rollback:** trocar `IMAGE_TAG` pela versão anterior e repetir `pull` + `up -d` (não depende do pipeline estar disponível).

## Backup e restauração (BL-29, RNF-08)

```bash
cd 05_infra
./backup/backup-db.sh                                   # produção (docker-compose.prod.yml)
COMPOSE_FILE=docker-compose.yml ./backup/backup-db.sh   # ambiente de desenvolvimento
./backup/restore-db.sh backup/dumps/garra-db-<carimbo>.dump
```

- `backup-db.sh` gera dump lógico (`pg_dump --format=custom`) em `backup/dumps/` e espelha o bucket MinIO em `backup/objetos/`. A retenção (`RETENCAO_DIAS`, default 30) só é aplicada **depois** de um dump válido, para nunca apagar o último backup bom por causa de uma execução que falhou.
- `restore-db.sh` é destrutivo: exige digitar `RESTAURAR`, salva um dump `pre-restore-*` do estado atual e para `backend`/`frontend` durante a operação. Se o dump `pre-restore` falhar ou sair vazio, o restore **aborta antes de qualquer `pg_restore`** (DEC-45, proposta). Os `pre-restore-*` expiram pela mesma `RETENCAO_DIAS` dos dumps normais (aplicada pelo `backup-db.sh`).
- Override explícito, só para banco recém-criado/vazio sem cópia a preservar: `FORCAR_SEM_PRE_RESTORE=1 ./backup/restore-db.sh <dump>` (emite aviso e pula o pre-restore). Não é definido no `.env`, de propósito, para não ficar ativo por acidente.
- `backup/dumps/` e `backup/objetos/` contêm dados reais de clientes e **nunca** são versionados (`backup/.gitignore`). Copie-os para fora do host — o destino externo definitivo continua `[A ESCLARECER]` (RNF-08).

Agendamento sugerido no host (diário às 02:00):

```cron
0 2 * * * cd /home/deploy/garra-engenharia/05_infra && ./backup/backup-db.sh >> backup/backup.log 2>&1
```

Verificação dos scripts (T42, 2026-11-07): `bash 05_infra/backup/tests/test_backup_scripts.sh` usa stubs de `docker` e não toca em banco real (45 ok). Detalhes e propostas em [backup-verificacao.md](../00_docs/backlog-auto/backup-verificacao.md) e DEC-45.

Emissão de relatórios (T47, 2026-11-11): nenhuma variável de ambiente nova; `MAX_RELATORIO_SIZE_BYTES` (200 MB, DEC-48 P5) é constante de código, então nada muda em `.env.example`, compose ou `render.yaml` (ver [relatorio-env-deploy.md](../00_docs/backlog-auto/relatorio-env-deploy.md)).

Variáveis `LEGENDA_IA_*` (T40, DEC-42): as 8 de limite e teto da legenda por IA estão no `environment:` do backend em `docker-compose.yml`, `docker-compose.prod.yml` e `render.yaml`. **Atenção:** `docker-compose.prod.yml` linha 89 tem YAML inválido (R-16) e precisa de correção antes do deploy por VPS.

Variáveis `DEEPSEEK_*` (T63, 2026-11-11, DEC-49 proposta): `LEGENDA_IA_PROVEDOR` (`fake` ou `deepseek`), `DEEPSEEK_API_KEY` (segredo; no Render `sync: false`), `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODELO` e `DEEPSEEK_TIMEOUT_S` estão nos `.env.example`, no `docker-compose.yml` e no `render.yaml`. Fora de desenvolvimento, `fake` e `deepseek` sem chave resultam em 503 (ou falha na inicialização). `DEEPSEEK_ENVIAR_IMAGEM` (padrão `false`) também está nos três. Ver [v1-legenda-ia-deepseek.md](../00_docs/backlog-auto/v1-legenda-ia-deepseek.md). O banco local ainda precisa de `alembic upgrade head` (head `a9c3e5f7b1d2`) e a imagem `05_infra-backend` de `docker compose build backend` (R-19).

Variáveis do RAG da legenda IA (T69, DEC-53 proposta): `LEGENDA_IA_RAG_ATIVO` (padrão `true`) e `LEGENDA_IA_RAG_K` (padrão `3`) estão no `environment:` do backend em `docker-compose.yml`, em `render.yaml` e em `.env.example`. Depois do deploy, rode `alembic upgrade head` e, uma vez, `python -m app.scripts.ingerir_conhecimento_ia` (revise antes o `--dry-run --amostras 20`); sem isso as referências ficam vazias.

## Frontend no GitHub Pages (DEC-55)

Desde a DEC-55 o frontend não precisa mais do Render: é exportado como site estático (`output: "export"`) e publicado pelo workflow [`deploy-pages.yml`](../.github/workflows/deploy-pages.yml) em **https://rafaelroriz-age.github.io/garra-engenharia/** a cada push em `main` que toque `03_frontend/` (ou manualmente em Actions → *Deploy frontend (GitHub Pages)* → *Run workflow*).

Configuração (ação humana, uma vez):

1. GitHub → Settings → Pages → Build and deployment → **Source = GitHub Actions**. Repositório privado exige plano pago do GitHub para usar Pages.
2. No Render, serviço `garra-backend` → Environment: `BACKEND_CORS_ORIGINS` deve conter `https://rafaelroriz-age.github.io` (sem o path). Salve e redeploy.
3. Se a URL do backend mudar, edite `NEXT_PUBLIC_API_URL` em `deploy-pages.yml` (é embutida no bundle em build time).
4. Depois de validar o Pages: remova o bloco `garra-frontend` do `render.yaml`, suspenda/apague o serviço no Dashboard do Render, tire `main_front` da matrix de `sync-deploy-branches.yml` e apague `03_frontend/Dockerfile.render`.

## Deploy em produção (Render)

> O serviço `garra-frontend` abaixo está sendo substituído pelo GitHub Pages (seção anterior, DEC-55).

Resolve o bloqueio B-03/HT-03 (hospedagem) com Render como provedor de nuvem. Toda a infraestrutura é definida como código em [`../render.yaml`](../render.yaml) (Render Blueprint) — os recursos abaixo são criados e conectados automaticamente, sem segredo hardcoded no repositório. Desde a DEC-17 (2026-07-21), cada serviço observa uma branch dedicada do monorepo como gatilho de auto-deploy; desde a DEC-22 (2026-08-05), as branches de staging foram removidas e `main` é sincronizada automaticamente para `main_back`/`main_front` pelo workflow `sync-deploy-branches.yml`:

| Serviço | Tipo Render | Origem | Branch |
|---|---|---|---|
| `garra-backend` | Web Service (Docker) | `04_backend/Dockerfile.render` | `main_back` |
| `garra-frontend` | Web Service (Docker) | `03_frontend/Dockerfile.render` | `main_front` |
| `garra-db` | PostgreSQL gerenciado (produção) | plano `basic-256mb` | — |

Não há ambiente de staging no Render (removido na DEC-22 — nunca chegou a ser provisionado). Para recriá-lo, adicione novamente o bloco correspondente em `render.yaml` e as branches a partir de `main`.

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

## Variáveis da telemetria da legenda IA (T68, 2026-11-12)

`LEGENDA_IA_CACHE_TTL_H`, `DEEPSEEK_PRECO_ENTRADA_CACHE_HIT_USD`, `DEEPSEEK_PRECO_ENTRADA_CACHE_MISS_USD` e `DEEPSEEK_PRECO_SAIDA_USD` estão em `.env.example`, `docker-compose.yml` e `render.yaml`. Os preços reais dependem da tarefa humana IA-07. O banco de desenvolvimento precisa de `alembic upgrade head` (migration `b8d4f2a6c1e7`).

## Dados de demonstração e amostras (T64, 2026-11-12)

O seed `DEMO` roda dentro do container do backend, num banco separado, por exemplo `docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m app.scripts.seed_demo`. O gabarito exige `00_docs/convertidos/RFO_INSPECAO.md`, ausente da imagem (contexto de build é `../04_backend`). A migration `e5a1f0c2b7d4` falha no banco de desenvolvimento por duas linhas `BENCH-01` duplicadas em `relatorios` (R-21).

## Dimensionamento do worker de relatórios (T17, 2026-11-04)

O benchmark dos pipelines finais (`00_docs/backlog-auto/benchmark-pipelines-finais.md`) mediu pico de RSS de 320 a 420 MB para um PDF de ~200 páginas e ~500 MB com PDF e DOCX em paralelo. Uma instância de 512 MB não comporta isso com folga: o worker deve ter **≥ 1 GB de RAM** (proposta DEC-40). Os PDF/DOCX das vistorias passam de 25 MB (37–38 MB e 30–31 MB), então o limite de upload de artefatos precisa ser separado do limite de foto.

## Runtime local no PC (DEC-57) — estado em 2026-11-17

- Entregues: `local/garra-local.ps1` (runtime, `install`/`uninstall`/`agente`) e `local/garra-agente.ps1` (túnel, `api.json`, snapshot, backup) — [agente-inicializacao.md](../00_docs/backlog-auto/agente-inicializacao.md); storage em disco com download assinado (`STORAGE_PROVEDOR`, T80) — [storage-local.md](../00_docs/backlog-auto/storage-local.md).
- Pendentes: importação do Render (T84, `importar-render.ps1` ainda inexistente), aposentadoria de `render.yaml` e da seção "Deploy em produção (Render)" (T85), E2E do modo leitura (T86), Neon (T87/T88, sem DEC-58 registrada). Até lá a seção do Render acima continua vigente.
