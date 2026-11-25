# T115 · Conferência de variáveis do Render x código (go-live)

- Tarefa: T115 (Engenheiro DevOps). Data: 2026-11-24. Branch: `worktree-backlog-T115`.
- Escopo: comparar `04_backend/app/core/config.py`, `04_backend/render-start.sh`, `00_docs/backlog-auto/golive-backend.md` (§5), `05_infra/.env.render.example` e `00_docs/backlog-auto/golive-runbook.md`. Serviço do Render observa `main_back`.
- Arquivos alterados: `05_infra/.env.render.example`, `00_docs/backlog-auto/golive-runbook.md`, este Doc. Código de aplicação não foi tocado.

## Divergências encontradas e correções

| # | Onde | Divergência | Correção |
|---|---|---|---|
| 1 | `.env.render.example` | Não listava `SEED_ON_STARTUP`/`ADMIN_SENHA`, e o comentário dizia que o seed era só manual; `golive-backend.md` §5 recomenda `SEED_ON_STARTUP=true`. | Adicionadas `SEED_ON_STARTUP=true`, `ADMIN_SENHA=` (vazia, segredo) e `ADMIN_EMAIL`; comentário alinhado ao §5. Comando manual mantido como alternativa. |
| 2 | `golive-runbook.md` passo 6 | Só descrevia o seed manual via Shell. | Passo passa a usar a flag `SEED_ON_STARTUP` + `ADMIN_SENHA` (boot), com o manual como alternativa. |
| 3 | `golive-runbook.md` "Não validado" | Dizia que `STORAGE_LOCAL_DIR` e o seed dependiam de confirmação do T110. | Marcado como confirmado em `config.py`/`bootstrap.py`. |

## Conferido sem divergência

- `ENVIRONMENT=production`, `JWT_SECRET_KEY` (validação fail-closed: default ou < 32 caracteres recusa o boot), `BACKEND_CORS_ORIGINS` sem `*`.
- `POSTGRES_*` e `POSTGRES_SSL=false` (padrão de `config.py`; Postgres interno do Render não usa TLS).
- `STORAGE_PROVEDOR=local` + `STORAGE_LOCAL_DIR=/var/data/storage` dentro do disco `/var/data` (padrão do código é relativo e sumiria a cada deploy).
- `RUN_MIGRATIONS_ON_STARTUP=true` (lido por `config.py`; `render-start.sh` sobe o uvicorn sem Pre-Deploy).
- `render-start.sh`: como root só cria `STORAGE_LOCAL_DIR` e troca para `appuser` via `setpriv`; usa `PORT` injetada pelo Render. Nenhuma variável nova exigida.
- `04_backend/Dockerfile.render` e `app/scripts/seed_admin.py` existem nos caminhos citados.
- Nenhum segredo, chave ou valor real foi escrito nos arquivos; os campos sensíveis ficam vazios.

## Decisão proposta (não aplicada)

- Propor ao integrador: `SEED_ON_STARTUP=true` como recomendado no go-live (já é o que o §5 do `golive-backend.md` diz). Não é decisão nova: registrar só se o integrador quiser formalizar em `decisoes.md` (DEC-59 já cobre o go-live).

## Verificação

- `pytest` e `ruff check .` (04_backend) e `npm run lint`/`npm run build` (03_frontend): **não rodados**, porque a tarefa só toca `05_infra/` e `00_docs/` (sem código de backend ou frontend). O checklist do PR se aplica à parte tocada.
- Nenhum teste contra o Render ou a rede (sem acesso por instrução).
