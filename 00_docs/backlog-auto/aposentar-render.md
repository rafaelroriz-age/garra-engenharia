# T85 · Documentação do novo deploy e aposentadoria dos artefatos do Render (DEC-57)

- Tarefa: T85 (papel devops), Bloco G do `BACKLOG.md`. Decisão de origem: DEC-57 (P1, P3, P4, P5).
- Data: 2026-11-17. Branch: `worktree-backlog-T85`.
- Depende de: T80, T82, T83, T84 (todas com Doc em `00_docs/backlog-auto/`).
- Sem alteração de código de aplicação (`04_backend/app`, `03_frontend/app|components|lib`): só infra, workflows, documentação e remoção dos artefatos do Render.

## 1. O que foi feito

| Item do campo Pronto | Feito | Onde |
|---|---|---|
| Seção "Produção no PC (DEC-57)" no `05_infra/README.md`: arquitetura, instalação do zero, operação diária, restauração em outro PC, PC desligado | Sim | `05_infra/README.md`, seção "Produção no PC (DEC-57)" |
| Seção antiga do Render vira nota histórica curta | Sim | `05_infra/README.md`, seção "Render (histórico — aposentado pela DEC-57, T85)"; as seções de Blueprint e passo a passo do Render foram removidas |
| `00_docs/configuracao.md` lista as variáveis novas | Sim | `00_docs/configuracao.md`, §7 (tabela com padrão e consumidor; colunas R/RE marcadas como históricas) |
| `render.yaml` removido | Sim | `git rm render.yaml` |
| `03_frontend/Dockerfile.render` e `04_backend/Dockerfile.render` removidos | Sim | `git rm` |
| `sync-deploy-branches.yml` desativado com comentário, não apagado | Sim | trigger `push` trocado por `workflow_dispatch`; job com `if: false`; comentário explica o motivo |
| `grep -ri onrender` no repo só encontra notas históricas em `00_docs/` | Sim (ver §3) | |
| `npm run build` e `pytest` continuam verdes | `npm run lint` e `npm run build`: verdes. `pytest`: **não verde neste PC**, ver §4 | |

Arquivo extra removido: `05_infra/.env.render.example` (checklist do Render, não lido por nenhum processo). Não estava no campo Toca, mas é artefato do Render e a tarefa manda aposentar os artefatos.

## 2. Referências tratadas (grep)

Busca: `render.yaml`, `Dockerfile.render`, `onrender`, `main_front`, `main_back` em `.github/`, `03_frontend/`, `04_backend/`, `05_infra/`.

| Arquivo | Referência | Tratamento |
|---|---|---|
| `render.yaml` (raiz) | Blueprint | removido |
| `03_frontend/Dockerfile.render`, `04_backend/Dockerfile.render` | imagens de produção do Render | removidos |
| `05_infra/.env.render.example` | checklist de variáveis do Render | removido |
| `.github/workflows/sync-deploy-branches.yml` | sincronização `main` → `main_back`/`main_front` | desativado (`workflow_dispatch` + `if: false`), comentário explicativo |
| `.github/workflows/ci.yml` | gatilho `push` em `main_front`, `main_back` | removido do gatilho (fica `[main]`); comentário atualizado |
| `.github/workflows/cd-production.yml`, `cd-staging.yml` | comentários sobre `render.yaml`/auto-deploy | comentário marcado como histórico; o workflow continua manual (VPS) |
| `05_infra/docker-compose.prod.yml` | comentário "código em render.yaml" | comentário atualizado (aposentado no T85) |
| `05_infra/local/garra-local.ps1` | comentário citando `Dockerfile.render` | comentário atualizado |
| `05_infra/README.md` | várias menções a `render.yaml`, Blueprint, Dashboard, `garra-frontend`, `garra-backend` | seção de Blueprint e passo a passo removidos; menções restantes reescritas (ver §1) |
| `04_backend/README.md` (linha da tabela da legenda IA) | "ainda não repassadas pelo compose/`render.yaml`" | trocado por "pelo `docker-compose.yml`" |
| `00_docs/configuracao.md` | `render.yaml`, `.env.render.example` no frontmatter e colunas R/RE | frontmatter atualizado; colunas marcadas como históricas em §7 |
| `03_frontend/` | nenhuma referência restante | — |
| `04_backend/` | nenhuma referência restante | — |

**Histórico mantido em `00_docs/`** (conforme a Pronto): `00_docs/configuracao.md` (colunas R/RE e divergências), `00_docs/backlog-auto/*.md` (T79–T84 e os demais Docs que citam Render como contexto), `00_docs/projeto/decisoes.md` (DEC-16, DEC-17, DEC-22, DEC-55, DEC-57). Não editados: `decisoes.md`, `status.md`, `riscos.md` (fechamento de lote).

Medida de "onrender" fora de `00_docs/`: após o commit, o grep feito no worktree não encontra mais `onrender` em `.github/`, `03_frontend/`, `04_backend/` e `05_infra/` (ver §3).

## 3. Conferência com grep

Executado no worktree depois das alterações (comandos e saída resumida):

Resultado (exceto `node_modules`, ignorado pelo git): restam só referências intencionais:

- `.github/workflows/sync-deploy-branches.yml`: comentários e nome do workflow, com o job em `if: false` e o gatilho `workflow_dispatch`.
- `.github/workflows/ci.yml`: comentário explicando que `main_back`/`main_front` foram aposentadas.
- `.github/workflows/cd-production.yml`, `cd-staging.yml`: comentários "HISTÓRICO".
- `05_infra/docker-compose.prod.yml`: comentário "aposentado no T85".
- `05_infra/README.md`: seção "Render (histórico)" e o passo 4 da configuração do Pages (registro do que foi removido).
- `03_frontend/` e `04_backend/`: nenhuma referência de deploy restante.

## 4. Testes do projeto (checklist do PR)

Ambiente deste PC: o venv `04_backend\.venv` do checkout principal (OneDrive) foi usado a partir do worktree, porque o worktree não tem venv. Banco: `garra_engenharia_test` no PostgreSQL de `05_infra` (localhost:5433, porta aberta), `alembic upgrade head` executado antes.

- **Frontend** (`03_frontend`, `npm ci` feito no worktree):
  - `npm run lint`: `✔ No ESLint warnings or errors`.
  - `npm run build`: `✓ Compiled successfully`, 16 páginas estáticas geradas. Verde.
- **Backend** (`04_backend`):
  - `ruff check .`: `All checks passed!`. Verde.
  - `pytest`: **não verde neste PC**. Comando: `python -m pytest -q -p no:warnings --continue-on-collection-errors --tb=line` em `04_backend`, com `POSTGRES_DB=garra_engenharia_test` e `WEASYPRINT_DLL_DIRECTORIES=%LOCALAPPDATA%\garra\msys64\ucrt64\bin`. Saída final (log completo em `$CLAUDE_JOB_DIR/tmp/pytest-T85.log`, não versionado):

    ```text
    32 failed, 445 passed, 14 skipped, 7 xfailed, 328 errors in 380.35s (0:06:20)
    ```

  - Causas observadas no log (contagem aproximada de linhas de erro):
    1. Maioria dos erros e falhas de fixture de banco: `asyncpg.exceptions.ConnectionDoesNotExistError` / `ConnectionResetError: [WinError 64]` (≈320 ocorrências). É o loop asyncio do Windows com asyncpg, não o código de aplicação.
    2. `OSError: [Errno 22] Invalid argument` ao importar `weasyprint` → `tinycss2` a partir do venv dentro do OneDrive (14 ocorrências; `tests/test_rfo_contexto.py` não coleta). Mesmo padrão de `ltip-pipeline.md` (linha 84).
    3. `RuntimeError: There is ...` (26 ocorrências; não investigado).
  - `alembic upgrade head` no banco de teste também caiu com `ConnectionDoesNotExistError`, então o head não foi confirmado nesta sessão.
  - Como nenhuma linha de Python foi alterada no T85, esses resultados não vêm das mudanças desta tarefa. Ainda assim, **não consegui provar que o estado anterior ao T85 dá o mesmo resultado** (não rodei na `main` por causa do custo e do venv). Isso fica pendente.
  - Para fechar: rodar `pytest` com o venv fora do OneDrive (ex.: `%LOCALAPPDATA%\garra\venv`), confirmar `alembic upgrade head` e comparar com a `main`.

## 5. Registro do que foi conferido

- `npm run lint` e `npm run build`: verdes (§4).
- `ruff check .`: verde (§4).
- `pytest`: não concluído neste PC (§4). Pendente.
- Nenhum `.env`, chave ou token foi criado ou versionado. `05_infra/local/.env` não existe no worktree.

## 6. Propostas para o fechamento de lote (não aplicadas em `decisoes.md`)

- **Proposta DEC-57 (complemento P6)**: "A produção no PC é o único ambiente de produção. `render.yaml`, `Dockerfile.render`, `05_infra/.env.render.example` e a sincronização `main` → `main_back`/`main_front` foram removidos ou desativados (T85). As branches `main_back`/`main_front`/`staging_*` não são mais usadas; se existirem no remoto, podem ser apagadas por um humano."
- **Proposta de risco**: o `pytest` no PC do dono roda a partir de um venv dentro do OneDrive, com `OSError [Errno 22]` ao importar `weasyprint`/`tinycss2`. Sugerir mover o venv de testes para `%LOCALAPPDATA%` (o mesmo critério que o T79 aplicou ao cluster e ao Pango). Registrar em `riscos.md` no fechamento.
- **Ação humana (HT-16)**: apagar os serviços `garra-backend`, `garra-frontend` e `garra-db` no Dashboard do Render somente depois de validar o app no PC e de conferir a importação (T84, exit 0). Não foi feito aqui.
- **Ação humana**: nas configurações do GitHub, remover `main_front`/`main_back` do remoto e revisar a branch protection, se ela citar essas branches.

## 7. Limitações

- Restauração de backup em outro PC (`05_infra/README.md`, "Restaurar backup em outro PC") está escrita, mas não foi executada de ponta a ponta. Marcada como "validar no primeiro uso".
- `ci.yml` continua rodando `pytest` no Ubuntu (CI); a mudança de gatilho não altera os jobs.
- Não foi possível confirmar, a partir do worktree, se o remoto ainda tem `main_front`/`main_back`/`staging_*` (sem acesso ao GitHub nesta sessão).
