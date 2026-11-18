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
├── nginx/
│   └── nginx.conf           # ✅ Reverse proxy + HTTPS (BL-27)
├── backup/
│   ├── backup-db.sh         # ✅ Dump do Postgres + espelho do MinIO (BL-29)
│   └── restore-db.sh        # ✅ Restore com confirmação e dump prévio (BL-29)
└── README.md                # Pré-requisitos, como rodar localmente, deploy e rollback
```

## Deploy em VPS próprio (alternativa à produção no PC — BL-27)

A produção oficial roda no PC do dono (seção "Produção no PC (DEC-57)"). `docker-compose.prod.yml` + `nginx/nginx.conf` ficam como caminho alternativo de VPS próprio (DEC-14/DEC-17), usado pelos workflows manuais `cd-staging.yml`/`cd-production.yml`.

**Limite de corpo no nginx (T102, DEC-39):** `client_max_body_size` padrão `1m`; só `/api/v1/fotos/upload` e `/upload-clipboard` aceitam `40m` (teto do backend: 25 MiB). Atenção: o upload de documentos de edificação (até 25 MiB) recebe 413 nesta stack até ganhar `location` própria (R-25). `nginx -t` não foi executado. Doc: [nginx-limite-corpo-fotos.md](../00_docs/backlog-auto/nginx-limite-corpo-fotos.md).

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

Emissão de relatórios (T47, 2026-11-11): nenhuma variável de ambiente nova; `MAX_RELATORIO_SIZE_BYTES` (200 MB, DEC-48 P5) é constante de código, então nada muda em `.env.example`, compose (ver [relatorio-env-deploy.md](../00_docs/backlog-auto/relatorio-env-deploy.md)).

Variáveis `LEGENDA_IA_*` (T40, DEC-42): as 8 de limite e teto da legenda por IA estão no `environment:` do backend em `docker-compose.yml`, `docker-compose.prod.yml`. **Atenção:** `docker-compose.prod.yml` linha 89 tem YAML inválido (R-16) e precisa de correção antes do deploy por VPS.

Variáveis `DEEPSEEK_*` (T63, 2026-11-11, DEC-49 proposta): `LEGENDA_IA_PROVEDOR` (`fake` ou `deepseek`), `DEEPSEEK_API_KEY` (segredo), `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODELO` e `DEEPSEEK_TIMEOUT_S` estão nos `.env.example`, no `docker-compose.yml`. Fora de desenvolvimento, `fake` e `deepseek` sem chave resultam em 503 (ou falha na inicialização). `DEEPSEEK_ENVIAR_IMAGEM` (padrão `false`) também está nos três. Ver [v1-legenda-ia-deepseek.md](../00_docs/backlog-auto/v1-legenda-ia-deepseek.md). O banco local ainda precisa de `alembic upgrade head` (head `a9c3e5f7b1d2`) e a imagem `05_infra-backend` de `docker compose build backend` (R-19).

Variáveis do RAG da legenda IA (T69, DEC-53 proposta): `LEGENDA_IA_RAG_ATIVO` (padrão `true`) e `LEGENDA_IA_RAG_K` (padrão `3`) estão no `environment:` do backend em `docker-compose.yml`, em `.env.example`. Depois do deploy, rode `alembic upgrade head` e, uma vez, `python -m app.scripts.ingerir_conhecimento_ia` (revise antes o `--dry-run --amostras 20`); sem isso as referências ficam vazias.

## Frontend no GitHub Pages (DEC-55)

Desde a DEC-55 o frontend não precisa mais do Render: é exportado como site estático (`output: "export"`) e publicado pelo workflow [`deploy-pages.yml`](../.github/workflows/deploy-pages.yml) em **https://rafaelroriz-age.github.io/garra-engenharia/** a cada push em `main` que toque `03_frontend/` (ou manualmente em Actions → *Deploy frontend (GitHub Pages)* → *Run workflow*).

Configuração (ação humana, uma vez):

1. GitHub → Settings → Pages → Build and deployment → **Source = GitHub Actions**. Repositório privado exige plano pago do GitHub para usar Pages.
2. Em `05_infra/local/.env`, `BACKEND_CORS_ORIGINS` deve conter `https://rafaelroriz-age.github.io` (sem o path). Reinicie com `garra-local.ps1 stop` e depois `start`.
3. Se a URL do backend mudar, edite `NEXT_PUBLIC_API_URL` em `deploy-pages.yml` (é embutida no bundle em build time).
4. Render aposentado (T85, DEC-57): `render.yaml`, `03_frontend/Dockerfile.render` e `04_backend/Dockerfile.render` foram removidos, e `sync-deploy-branches.yml` foi desativado. Os serviços no Dashboard do Render devem ser apagados por um humano depois que o app for validado no PC (HT-16).

## Render (histórico — aposentado pela DEC-57, T85)

Até 2026-11-17 o backend e o banco rodaram no Render (`garra-backend`, `garra-frontend`, `garra-db`), definidos no Blueprint `render.yaml` e nos `Dockerfile.render`, com auto-deploy pelas branches `main_back`/`main_front`. Isso foi aposentado: `render.yaml`, `03_frontend/Dockerfile.render`, `04_backend/Dockerfile.render` e `05_infra/.env.render.example` foram removidos, e `sync-deploy-branches.yml` foi desativado. O que existia continua no histórico do git anterior ao T85. A migração dos dados do Render para o PC está em [importar-render.md](../00_docs/backlog-auto/importar-render.md) (T84). Nada aqui é mais executado; a produção atual é a seção abaixo.

## Produção no PC (DEC-57)

Desde a DEC-57 a produção roda no PC do dono, sem Docker e sem Render. Detalhes: [runtime-local-pc.md](../00_docs/backlog-auto/runtime-local-pc.md) (T79), [storage-local.md](../00_docs/backlog-auto/storage-local.md) (T80), [snapshot-cifrado.md](../00_docs/backlog-auto/snapshot-cifrado.md) (T81), [agente-inicializacao.md](../00_docs/backlog-auto/agente-inicializacao.md) (T82) e [front-modo-leitura.md](../00_docs/backlog-auto/front-modo-leitura.md) (T83).

### Arquitetura

- **Backend e banco no PC**: FastAPI (`uvicorn` em `127.0.0.1:UVICORN_PORT`, padrão 8000) e, desde a DEC-58, o banco **Neon** (`POSTGRES_MODO=neon`, seção "Banco no Neon (DEC-58)"). O PostgreSQL 16 portátil (porta 5434; cluster em `%LOCALAPPDATA%\garra\pgdata`, fora do OneDrive) é o modo `POSTGRES_MODO=local`, opcional/fallback. Arquivos em `05_infra/local/storage/`.
- **Exposição**: `cloudflared tunnel --url` aponta para o uvicorn. A URL `https://*.trycloudflare.com` muda a cada boot e é publicada em `api.json` na branch órfã `snapshot` deste repositório.
- **Front**: site estático no GitHub Pages (`https://rafaelroriz-age.github.io/garra-engenharia/`, `deploy-pages.yml`, DEC-55). Ele lê `api.json` e aponta para a API atual.
- **Modo leitura**: `snapshot.enc` (AES-256-GCM; chave PBKDF2-SHA256 a partir de `SNAPSHOT_SENHA`) é publicado junto com as respostas de leitura. Sem PC online, o site abre em modo leitura, pede a senha da equipe e bloqueia gravações.
- **Agente**: tarefa agendada `Garra Local` (logon do Windows, `garra-agente.ps1`). Faz `git pull --ff-only` em `main` (só com o worktree limpo), sobe o backend e o túnel, publica `api.json` e `snapshot.enc`, e faz heartbeat e backup diário.

Versionados: `05_infra/local/garra-local.ps1`, `garra-agente.ps1`, `importar-render.ps1` e `.env.example`. Fora do git (`.gitignore`): `05_infra/local/.env`, `bin/`, `backups/`, `storage/`, `logs/`, `run/` e `04_backend/.venv-prod/`.

### Instalação do zero (PC novo ou reinstalação)

Pré-requisitos: Windows 10/11, Python 3.12 (`py -3.12`), Git, `cloudflared` no PATH e acesso ao repositório. Comandos a partir da raiz do repositório, em PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 setup
# editar 05_infra\local\.env: definir SNAPSHOT_SENHA (>= 16 caracteres, senha da equipe)
powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 start
powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 install --dry
powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 install
```

- `setup` cria o `.env` (gera `POSTGRES_PASSWORD`, `JWT_SECRET_KEY` e `ADMIN_SENHA` só se estiverem vazias), baixa o PostgreSQL, cria o cluster e o venv `04_backend\.venv-prod`, e instala o Pango para o WeasyPrint (PDF). `setup -PularPango` pula o Pango: o PDF fica indisponível e o DOCX funciona.
- Se `pgdata` já existe e `.env` não, o `setup` aborta de propósito, para não gerar senha nova para um cluster existente.
- Para trazer o banco do Render (HT-15), rode `importar-render.ps1` depois de `start` (T84).
- `install --dry` mostra o que será registrado sem registrar nada. `install` pode exigir PowerShell como administrador na primeira vez, se o Windows negar o registro da tarefa.

### Operação diária

| Ação | Comando |
|---|---|
| Ver estado (Postgres, uvicorn, `/health`) | `garra-local.ps1 status` |
| Subir manualmente (sem a tarefa agendada) | `garra-local.ps1 start` |
| Backup manual | `garra-local.ps1 backup` (`05_infra\local\backups\garra-AAAAMMDD-HHmm.dump`; retenção `BACKUP_RETENCAO`, padrão 14) |
| Parar backend e banco | `garra-local.ps1 stop` |
| Agente em primeiro plano (depuração) | `garra-local.ps1 agente` |
| Remover a tarefa agendada | `garra-local.ps1 uninstall` (não para o Postgres; use `stop`) |

Logs em `05_infra\local\logs\`: `garra-local.log`, `garra-agente.log`, `postgres.log` e `uvicorn-*.out/err.log`.

**Porta 8000:** se o Docker Desktop de desenvolvimento estiver publicando a 8000, o `start` recusa subir e informa quem ocupa a porta. Pare o compose de dev ou defina outra `UVICORN_PORT` no `.env`; o agente usa a mesma variável no túnel.

### Restaurar backup em outro PC

Procedimento não executado de ponta a ponta nesta versão; validar no primeiro uso.

1. Espere o OneDrive sincronizar e escolha o dump mais recente em `05_infra\local\backups\` (`garra-*.dump`; `render-final-*.dump` é o retrato do Render).
2. No PC novo, rode `setup`. Se o `.env` foi copiado do PC antigo, mantenha as senhas dele.
3. Com o Postgres no ar, restaure no banco `garra_producao` vazio, usando o `pg_restore` de `05_infra\local\bin\pgsql\bin`: `pg_restore -h localhost -p 5434 -U garra -d garra_producao --clean --if-exists <arquivo.dump>`. A senha vem de `PGPASSWORD` (`.env`).
4. Rode `start` e confira com `status`. As migrações do `start` completam o schema se o dump for de uma versão anterior.
5. Rode `install` para reativar a tarefa agendada e o túnel.

### PC desligado

- O site abre em **modo leitura** com o último `snapshot.enc`: pede a senha da equipe, mostra os dados do snapshot e desabilita todas as gravações. O snapshot não tem fotos, documentos nem portal do cliente.
- Quando o PC volta e o agente publica de novo, o front sai do modo leitura sozinho.
- Se o processo do agente morrer à força, `online:false` não é publicado. Por isso o front trata um `heartbeat` mais antigo que ~25 min como offline.
- O portal do cliente só funciona com o PC ligado.

## Banco no Neon (DEC-58)

Desde a DEC-58 o banco de produção é um projeto **Neon** (Postgres gerenciado, plano gratuito). O backend continua no PC do dono (túnel, `api.json`, `snapshot.enc` e front no Pages, como na DEC-57). Detalhes de implementação: [neon-banco.md](../00_docs/backlog-auto/neon-banco.md) (T87), [migrar-render-neon.md](../00_docs/backlog-auto/migrar-render-neon.md) (T88) e [neon-backup.md](../00_docs/backlog-auto/neon-backup.md) (T89).

O Postgres portátil do PC (DEC-57 P1) passa a ser **opcional e fallback**: continua disponível com `POSTGRES_MODO=local`, mas não é mais o banco de produção.

### Criar e conectar

1. No console do Neon, crie o projeto (região próxima, por exemplo São Paulo).
2. Copie a connection string **direta**: desligue o toggle "Pooled connection". O host **não** pode ter `-pooler`: o asyncpg não funciona com o PgBouncer, e o `garra-local.ps1` recusa esse host.
3. No `05_infra\local\.env` (fora do git), preencha com os valores do seu projeto, nunca no `.env.example` nem em arquivo versionado:

   ```
   POSTGRES_MODO=neon
   POSTGRES_HOST=<host direto do Neon, sem -pooler>
   POSTGRES_PORT=5432
   POSTGRES_USER=<usuario>
   POSTGRES_PASSWORD=<senha>
   POSTGRES_DB=<banco>
   POSTGRES_SSL=true
   ```

4. Rode `garra-local.ps1 setup` (instala o venv, o Pango e os binários `pg_dump`/`pg_restore`/`psql`, sem initdb), depois `start` (aplica `alembic upgrade head` no Neon e os seeds) e confira com `status`: `neon: conectado (neon-ok tls=True)`.

### Operação

- **`POSTGRES_SSL=true` é obrigatório no Neon.** Acrescenta `?ssl=require` à URL do banco (`config.py`). O `alembic`, as migrations e o backend usam a mesma URL.
- **Storage de arquivos fora do Neon (por ora):** o Neon também oferece bucket, mas a DEC-58 (P5) mantém fotos e relatórios no MinIO/S3-compatível (`MINIO_*`) ou no disco local (`STORAGE_PROVEDOR=local`). Só o banco está no Neon; migrar o bucket é evolução futura.
- **Cold start:** o Neon escala a zero após ociosidade (cerca de 5 min). A primeira conexão pode levar 1 a 2 s, ou falhar. Se o `start` falhar, rode de novo.
- **Backup:** o plano gratuito do Neon **não substitui backup próprio**. `garra-local.ps1 backup` (e a rotina diária do agente, T82) faz `pg_dump -Fc` contra o Neon com `PGSSLMODE=require`, grava em `05_infra\local\backups\garra-AAAAMMDD-HHmm.dump` e mantém os últimos `BACKUP_RETENCAO` (padrão 14). O `pg_dump` precisa ser de versão igual ou maior que a do servidor Neon. O setup instala o PostgreSQL 16 portátil; se o servidor estiver em versão maior, o `pg_dump` recusa e o log mostra a versão.
- **Restaurar em outro banco:** use o `pg_restore` de `05_infra\local\bin\pgsql\bin` com `PGSSLMODE=require` e a conexão direta do banco de destino (sem escrever a URL em arquivo ou no histórico):

  ```powershell
  $env:PGPASSWORD = '<senha>'; $env:PGSSLMODE = 'require'
  & .\05_infra\local\bin\pgsql\bin\pg_restore.exe -h <host-direto> -p 5432 -U <usuario> -d <banco> --clean --if-exists --no-owner --no-privileges <arquivo.dump>
  ```

  Para trazer dados do Render, use `importar-render.ps1 -DestinoPrompt` (T88), que pede as URLs com entrada oculta.
- **Dumps são dados pessoais** (usuários, hashes, fotos e documentos). Ficam em `05_infra\local\backups\`, que está no `.gitignore`, mas dentro da pasta sincronizada pelo OneDrive. Não copie para repositórios públicos.

## Referências

- Stack e ADRs de infraestrutura: [00_docs/arquitetura.md](../00_docs/arquitetura.md)
- Decisão de estrutura de pastas: [00_docs/projeto/decisoes.md](../00_docs/projeto/decisoes.md) (DEC-09)
- Prompt de setup: [.github/prompts/14-setup-ambiente-desenvolvimento.prompt.md](../.github/prompts/14-setup-ambiente-desenvolvimento.prompt.md)
- Prompt de DevOps: [.github/prompts/12-devops.prompt.md](../.github/prompts/12-devops.prompt.md)

## Variáveis da telemetria da legenda IA (T68, 2026-11-12)

`LEGENDA_IA_CACHE_TTL_H`, `DEEPSEEK_PRECO_ENTRADA_CACHE_HIT_USD`, `DEEPSEEK_PRECO_ENTRADA_CACHE_MISS_USD` e `DEEPSEEK_PRECO_SAIDA_USD` estão em `.env.example`, `docker-compose.yml`. Os preços reais dependem da tarefa humana IA-07. O banco de desenvolvimento precisa de `alembic upgrade head` (migration `b8d4f2a6c1e7`).

## Dados de demonstração e amostras (T64, 2026-11-12)

O seed `DEMO` roda dentro do container do backend, num banco separado, por exemplo `docker exec -e POSTGRES_DB=garra_demo_v1 garra-backend python -m app.scripts.seed_demo`. O gabarito exige `00_docs/convertidos/RFO_INSPECAO.md`, ausente da imagem (contexto de build é `../04_backend`). A migration `e5a1f0c2b7d4` falha no banco de desenvolvimento por duas linhas `BENCH-01` duplicadas em `relatorios` (R-21).

## Dimensionamento do worker de relatórios (T17, 2026-11-04)

O benchmark dos pipelines finais (`00_docs/backlog-auto/benchmark-pipelines-finais.md`) mediu pico de RSS de 320 a 420 MB para um PDF de ~200 páginas e ~500 MB com PDF e DOCX em paralelo. Uma instância de 512 MB não comporta isso com folga: o worker deve ter **≥ 1 GB de RAM** (proposta DEC-40). Os PDF/DOCX das vistorias passam de 25 MB (37–38 MB e 30–31 MB), então o limite de upload de artefatos precisa ser separado do limite de foto.

## Runtime local no PC (DEC-57) — estado em 2026-11-17

- Entregues: `local/garra-local.ps1` (runtime, `install`/`uninstall`/`agente`) e `local/garra-agente.ps1` (túnel, `api.json`, snapshot, backup) — [agente-inicializacao.md](../00_docs/backlog-auto/agente-inicializacao.md); storage em disco com download assinado (`STORAGE_PROVEDOR`, T80) — [storage-local.md](../00_docs/backlog-auto/storage-local.md).
- Pendentes: importação do Render (T84, `importar-render.ps1` ainda inexistente), aposentadoria de `render.yaml` e da seção "Deploy em produção (Render)" (T85), E2E do modo leitura (T86), Neon (T87/T88, sem DEC-58 registrada). Até lá a seção do Render acima continua vigente.
