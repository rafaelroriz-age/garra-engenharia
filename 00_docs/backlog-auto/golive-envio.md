# T113 · Go-live: envio da `main` à origin

Data: 2026-11-24 · Branch do worktree: `worktree-backlog-T113`

## Situação: BLOQUEADA — a `main` não foi enviada

`git push origin main` foi recusado pela barreira (`.claude/settings.json`, hook
`backlog_auto.hooks guard`):

```text
Bloqueado pela barreira de dados do backlog-auto: [...] não faça push. Padrões: git push.
Para uma escrita legítima, peça a uma pessoa que defina BACKLOG_ESCRITA=1 na sessão.
```

A tarefa dizia que a barreira estava liberada, mas `BACKLOG_ESCRITA` estava vazia na sessão
(conferido em bash e PowerShell). A barreira não foi contornada e a variável não foi definida
pela sessão. O critério **Pronto não foi atingido**.

| Item | Estado em 2026-11-24 |
|---|---|
| `origin/main` | `4ce09c3` (inalterada) |
| `main` local | `c6f2fc6` |
| `git rev-list --count origin/main..main` | 23 |
| ci.yml, deploy-pages.yml, sync-deploy-branches.yml | **não acompanhados** (nada foi enviado) |
| `main_back` contém a `main` local | não (`origin/main_back` = `e2fe2e5`) |

## Conferências antes do envio

- `git status` limpo; `origin/main` é ancestral da `main` (envio é fast-forward, sem `--force`).
- 23 commits, 35 arquivos. Nenhum `.env` nem dump; só os modelos `04_backend/.env.example` e
  `05_infra/.env.render.example`. A busca por chaves/tokens nos patches achou apenas nomes de
  variáveis, valores vazios e valores de teste.
- `origin/main_back` não tem commit fora da `main`: não se espera conflito no sync.
- Os workflows `ci.yml`, `deploy-pages.yml` e `sync-deploy-branches.yml` constam como `active`
  (API pública do GitHub).
- `gh` está em `C:\Program Files\GitHub CLI\gh.exe`, mas **sem login** (`gh auth status`).

## CI que já falhava na origin

Em `4ce09c3` o run [CI 45496267601](https://github.com/rafaelroriz-age/garra-engenharia/actions/runs/45496267601)
falhou no job de backend, passo `Testes (pytest)`; frontend passou; E2E e Trivy foram pulados.
O deploy do Pages no mesmo commit teve **sucesso**, então não há ação pendente sobre o `Source`.

Enviar só a `main` atual repetiria a falha. O job foi reproduzido localmente (imagem do backend,
Postgres 16 e MinIO descartáveis, cópia do commit via `git archive`), e as causas foram
corrigidas nesta branch:

| Causa | Correção |
|---|---|
| O job não aplicava migrations (`relation "usuarios" does not exist` no 1º teste) | `ci.yml`: passo `alembic upgrade head` |
| O job não tinha MinIO (erros `botocore` em storage, fotos, legenda IA) | `ci.yml`: passo que sobe o MinIO e cria o bucket |
| A API sob teste reaproveitava conexão do pool entre event loops | `tests/conftest.py`: `AsyncSessionLocal` usa o engine `NullPool` |
| O vetor de snapshot comparava bytes de `gzip`, que variam por plataforma | `tests/test_snapshot.py`: compara os demais campos e o texto decifrado |
| **Defeito de produção:** o `weasyprint` liga `ImageFile.LOAD_TRUNCATED_IMAGES` no processo e o upload aceitava JPEG truncado (201 em vez de 422) | `app/services/image_processing.py` + `tests/test_imagem_truncada.py` |

Commits: `4cfcc01` (CI e testes) e `08ec82c` (foto truncada).

## Testes

| Execução | Resultado |
|---|---|
| Reprodução do CI, `08ec82c`, `pytest --maxfail` desligado (`-rfE`) | **897 passed, 3 skipped, 4 xfailed, 0 falhas** (350 s) |
| `ruff check .` (venv, Windows) | All checks passed! |
| Windows: `test_golive_boot`, `test_health`, `test_config_postgres_ssl`, `test_legenda_ia_retry_after` | 23 passed |
| Windows: `test_imagem_truncada` | 2 passed |
| `pytest` completo no Windows | não roda (falta `libpango` do WeasyPrint) |
| `npm run lint` / `npm run build` | não rodados: esta branch não toca `03_frontend` |

Limites da reprodução: os passos novos do `ci.yml` (MinIO com `--network host`) **não rodaram no
GitHub Actions**. Os jobs `docker-build-scan` (Trivy) e `e2e` dependem do backend verde, vinham
sendo pulados e **não foram verificados**; podem revelar falhas novas.

## Próximos passos (ação humana)

1. Integrar `worktree-backlog-T113` na `main` (traz as correções de CI).
2. Antes de enviar, ter em conta: o push dispara o sync `main` → `main_back`, e o Render observa
   `main_back`. O sync **não espera o CI**, então o envio já pode publicar o backend.
3. Enviar, num terminal próprio: `git push origin main`. Alternativa: reexecutar a T113 numa
   sessão iniciada com `BACKLOG_ESCRITA=1`.
4. Para acompanhar com `gh`: `gh auth login`, depois `gh run list` e `gh run watch`.
5. Conferir que `main_back` contém a `main`: `git fetch origin` e
   `git rev-list --count origin/main_back..origin/main` = 0.

## Para o fechamento de lote

- T113 continua pendente (bloqueada pela barreira), não `done`.
- `riscos.md`: o Render pode receber código com CI vermelho, porque o sync não depende do CI.
  Proposta de decisão: fazer `sync-deploy-branches.yml` disparar só após o CI passar
  (`workflow_run`).
- A variável de liberação precisa existir no ambiente da sessão; o texto da tarefa não a define.
