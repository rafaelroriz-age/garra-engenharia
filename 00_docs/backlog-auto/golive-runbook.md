# T112 · Runbook de go-live no Render + GitHub Pages (DEC-59)

- Tarefa: T112 (DevOps). Data: 2026-11-24. Branch: `worktree-backlog-T112`.
- Alvo: backend e Postgres no Render (`04_backend/Dockerfile.render`), front estático no GitHub Pages com API fixa. Sem Neon, sem PC local.
- Nada aqui foi executado contra o Render ou a rede. O runbook é para uma pessoa seguir no painel.
- Arquivos: `05_infra/.env.render.example` (nomes das variáveis, sem segredos), `05_infra/smoke/smoke.sh` (smoke-test), este Doc.

## Passos

1. **Dump do banco atual** (se houver dados a migrar). A partir de `05_infra/`, com o Postgres de origem no ar:
   `docker compose exec -T db pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > garra-AAAAMMDD.dump`.
   Guarde o arquivo fora do git. Os arquivos de fotos/laudos (storage local do PC) precisam ser copiados à parte, para o disco do passo 4.
2. **Criar o PostgreSQL no Render** (Dashboard > New > PostgreSQL). Anote host interno, porta, usuário, senha e nome do banco. Restaure o dump, se houver: `pg_restore --no-owner --clean --if-exists -d "<URL externa>" garra-AAAAMMDD.dump`. Sem dump, o schema nasce pelas migrations no boot (passo 5).
3. **Criar o serviço web** (New > Web Service > Docker): repositório `rafaelroriz-age/garra-engenharia`, **branch `main_back`** (recebe a `main` automaticamente depois que o CI passa), Dockerfile Path `./04_backend/Dockerfile.render`, Docker Build Context `./04_backend`, Health Check Path `/health`. Nome sugerido `garra-backend` (a URL padrão do front é `https://garra-backend.onrender.com`; se o Render der outro hostname, use-o no passo 7).
4. **Render Disk persistente**: no serviço, Disks > Add Disk, Mount Path `/var/data` (tamanho conforme o volume de fotos). Disco exige plano pago. Sem ele, os arquivos somem a cada deploy.
5. **Variáveis de ambiente** (Environment): preencher conforme `05_infra/.env.render.example`. Obrigatórias: `ENVIRONMENT=production`, `RUN_MIGRATIONS_ON_STARTUP=true` (o `preDeployCommand` do render.yaml antigo não existe mais; as migrations rodam no boot), `BACKEND_CORS_ORIGINS=https://rafaelroriz-age.github.io` (sem path), `POSTGRES_*`, `JWT_SECRET_KEY` (aleatório, longo), `STORAGE_PROVEDOR=local`, `STORAGE_LOCAL_DIR=/var/data/storage`. Salve e aguarde o deploy; confira os logs (migrations e "Application startup complete").
6. **Admin inicial e gabarito** (só se o banco for novo): no Environment, definir `SEED_ON_STARTUP=true` e `ADMIN_SENHA` (12+ caracteres, segredo próprio, nunca o padrão de dev); o boot roda os seeds idempotentes e cria o admin. Confira nos logs "Seed do admin no boot". Alternativa manual, se preferir não usar a flag: Shell do serviço, `ADMIN_EMAIL=... ADMIN_SENHA=... python -m app.scripts.seed_admin`.
7. **GitHub Pages**: Settings > Pages > Build and deployment > Source = **GitHub Actions**. Em Settings > Secrets and variables > Actions > **Variables**, criar `API_URL_PROD` = `https://<host-do-backend>/api/v1` (o `deploy-pages.yml` usa esse valor, com fallback `https://garra-backend.onrender.com/api/v1`). O `NEXT_PUBLIC_BASE_PATH` já é `/garra-engenharia` no workflow.
8. **Publicar o front**: o push na `main` com mudança em `03_frontend/**` dispara o workflow; sem mudança, rode manualmente Actions > "Deploy frontend (GitHub Pages)" > Run workflow. Confirme que a URL `https://rafaelroriz-age.github.io/garra-engenharia/` abre.
9. **Smoke-test**, de qualquer máquina com bash e curl:
   `API_URL=https://garra-backend.onrender.com ADMIN_EMAIL=<admin> ADMIN_SENHA=<senha> bash 05_infra/smoke/smoke.sh`
   Testa `/health`, login, `GET /api/v1/edificacoes` e preflight CORS com a origem do Pages. Saída 0 = tudo certo. A primeira chamada pode demorar (cold start).
10. **Teste manual curto**: abrir o front, entrar, listar edificações, abrir uma foto e gerar um PDF.

## Rollback

- **Backend**: Render > serviço > Events/Deploys > escolher o deploy anterior bom > Rollback. Se o problema for migration, restaurar o dump do passo 1 num banco novo e apontar `POSTGRES_*` para ele (as migrations têm `downgrade()`, mas o dump é o caminho seguro).
- **Front**: reverter o commit em `main` (`git revert`, sem force) e deixar o workflow republicar, ou rodar o workflow de um commit anterior. A API fixa é variável de repositório: corrigir `API_URL_PROD` e reexecutar o workflow resolve URL errada.
- **CORS ou variável errada**: corrigir em Environment e redeploy; não exige rebuild do front.
- **Storage**: não apague o Render Disk no rollback; ele é independente do deploy.

## Pontos de atenção

- `BACKEND_CORS_ORIGINS` leva só a origem (`https://rafaelroriz-age.github.io`), nunca `/garra-engenharia`.
- Plano gratuito do Render dorme após inatividade e não tem disco; para fotos persistentes usar plano pago ou `STORAGE_PROVEDOR=s3`.
- O `20930f5^:render.yaml` é só referência; não recriar na raiz (DEC-09).
- `STORAGE_LOCAL_DIR` confirmado em `app/core/config.py` (padrão `../05_infra/local/storage`, por isso o passo 5 exige `/var/data/storage`). Seed no boot: flag `SEED_ON_STARTUP` (passo 6), confirmada em `config.py` e `bootstrap.py`.

## Verificação feita

- `bash -n 05_infra/smoke/smoke.sh`: OK (sem erros de sintaxe).
- Testes de backend/frontend não rodados: a tarefa só toca docs e infra (sem código de aplicação).
- Rotas conferidas no código: `POST /api/v1/auth/login` (JSON `{email, senha}`, resposta com `access_token`), `GET /api/v1/edificacoes`, `GET /health`.
- Smoke-test não foi executado contra servidor real (sem rede, por instrução).
