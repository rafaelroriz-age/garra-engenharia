# T82 · Agente de inicialização: túnel, publicação e tarefa agendada (DEC-57)

## 1. O que foi entregue

| Arquivo | Conteúdo |
|---|---|
| `05_infra/local/garra-agente.ps1` | Agente (PowerShell 5.1, só ASCII): atualização, backend, túnel, publicação, laço e encerramento. |
| `05_infra/local/garra-local.ps1` | Novos subcomandos `install`, `uninstall`, `agente` (+ `-Dry`/`--dry`, `-SemIniciar`). |
| `05_infra/local/.env.example` | `GARRA_PUBLIC_REPO`, `GARRA_PUBLIC_TOKEN`, `AGENTE_HEARTBEAT_MIN`, `AGENTE_SNAPSHOT_MIN`, `AGENTE_TICK_SEG` (`SNAPSHOT_SENHA` já existia do T79/T81). |

## 2. Fluxo do agente

1. Mutex `Local\GarraAgente` (segunda instância sai).
2. `git pull --ff-only origin main` **só** se `git status --porcelain` vazio **e** branch atual `main`; senão loga WARN e segue com o código atual.
3. `pip install -r requirements.txt` no `.venv-prod` se o SHA-256 mudou (marca em `run/requirements.sha256`).
4. `garra-local.ps1 start` (Postgres, migrations, seeds, uvicorn).
5. `cloudflared tunnel --no-autoupdate --url http://127.0.0.1:<porta>`; a URL `https://*.trycloudflare.com` é extraída do log (`run/cloudflared.err.log`; ignora `api.trycloudflare.com`). PID em `run/cloudflared.pid` (cloudflared órfão de uma execução anterior é encerrado). Procura em PATH e em `C:\Program Files (x86)\cloudflared`.
6. Publica `api.json` `{url, api_base (url + /api/v1), online, desde, heartbeat}` e `snapshot.enc` (gerado com `python -m app.scripts.gerar_snapshot`; na 1ª vez sem `--somente-se-mudou`, depois com; código 3 = nada mudou, só heartbeat).
7. Laço (tick `AGENTE_TICK_SEG`=15 s): cloudflared morto → reinicia e republica a nova URL; `/health` sem resposta em 2 ticks → `garra-local.ps1 start`; heartbeat a cada 10 min; snapshot a cada 30 min; backup diário (`garra-local.ps1 backup`, marca em `run/ultimo-backup.txt`). Falha de push é WARN e é retentada em ~2 ticks.
8. Ao encerrar (Ctrl+C, fim normal ou `-UmaVez`) publica `online:false` e derruba o cloudflared.

**Limite conhecido:** se o processo for morto à força (Stop da tarefa, desligamento abrupto, `Stop-Process`), o `finally` não roda e `online:false` não é publicado. O front (T83) deve tratar `heartbeat` mais velho que ~25 min como offline (2 heartbeats + folga). Proposta para T83.

## 3. Publicação

Clone dedicado em `%LOCALAPPDATA%\garra\publico` (fora do repo). A cada publicação: `git rm --cached`, `git add api.json snapshot.enc`, `write-tree` + `commit-tree` (commit **sem pai**, equivalente a `checkout --orphan`), `update-ref refs/heads/snapshot` e `git push --force <url> snapshot:snapshot`. Na criação do clone faz um `fetch --depth 1` da branch `snapshot` para recuperar o `snapshot.enc` já publicado (reinstalação do PC); falha é tolerada.

- Com `GARRA_PUBLIC_TOKEN`: a URL de push `https://x-access-token:<token>@github.com/<repo>.git` é montada em memória a cada push; o remoto `origin` gravado no `.git/config` **não** tem token. O token entra na lista de segredos mascarados (`***`) do log. Fine-grained PAT só com Contents read/write no repo.
- Sem token: URL sem credencial, usa o Git Credential Manager. `GIT_TERMINAL_PROMPT=0` evita travar pedindo senha.
- **Actions:** nenhum workflow dispara em push na `snapshot`: `ci.yml` (push em `main_front/main_back/main`), `deploy-pages.yml` e `sync-deploy-branches.yml` (`main`), `cd-*` (tags `v*` / manual).

## 4. Tarefa agendada

`garra-local.ps1 install` → `Register-ScheduledTask "Garra Local"`:
- Ação: `powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ...\garra-agente.ps1`
- Gatilho `AtLogOn` do usuário atual; principal Interactive + RunLevel Limited (sem elevação); `RestartCount 5` / `RestartInterval 1 min`; sem limite de duração; roda na bateria; `MultipleInstances IgnoreNew`.
- Inicia a tarefa logo após registrar (`-SemIniciar` desativa).
- Se o Windows negar o registro, a mensagem orienta rodar `install` uma vez num PowerShell como administrador. **Não foi registrada nesta sessão** (HT-15: o dono roda).

`uninstall` para e remove a tarefa e encerra o cloudflared pelo PID gravado; Postgres/uvicorn continuam (use `stop`).

## 5. Comandos

```powershell
.\05_infra\local\garra-local.ps1 install --dry   # mostra o que seria registrado
.\05_infra\local\garra-local.ps1 install         # registra e inicia (HT-15)
.\05_infra\local\garra-local.ps1 uninstall
.\05_infra\local\garra-local.ps1 agente          # em primeiro plano, para depurar
```

Parâmetros de teste do `garra-agente.ps1`: `-RemotoAlternativo <caminho|url>`, `-UmaVez`, `-SemBackend`, `-SemAtualizar`, `-SemTunel -UrlFixa <url>`, `-SnapshotArquivo <arq>`, `-PastaPublico <dir>`. Logs: `05_infra/local/logs/garra-agente.log` (rotação em 5 MB, 3 anteriores; `garra-local.log` é rotacionado na partida do agente).

## 6. Testes executados (2026-11-17)

- **`install --dry`** e **`uninstall -Dry`**: imprimiram ação, diretório, gatilho `AtLogOn BSB02428L\dynatest`, Interactive/Limited, RestartCount 5/1 min; nada registrado.
- **Túnel real + publicação em remoto bare local** (`-UmaVez -SemBackend -SemAtualizar -RemotoAlternativo bare.git`): cloudflared real subiu em ~8 s, URL extraída (`https://monica-assembly-which-refer.trycloudflare.com`), publicado `online=True`, depois `online=False`. O bare ficou com **um único commit sem pai** na `snapshot` contendo `api.json` e `snapshot.enc`; `.git/config` do clone só tem o `origin` sem credencial; nenhum cloudflared sobrou.
- **Queda do túnel**: agente em laço (tick 3 s), cloudflared morto com `Stop-Process`; o agente logou `cloudflared caiu: reiniciando`, obteve nova URL (`jessica-beverages-uni-rural...`) e republicou `api.json` com ela (~10 s depois).
- **Não exercitado** (sem venv-prod/Postgres no worktree): `start` do backend, geração real do `snapshot.enc` (usado um arquivo fictício via `-SnapshotArquivo`), `pip install` por mudança do requirements, `git pull` (a branch do worktree não é `main`, caminho "pular" logado por construção), backup diário, push real ao GitHub (proibido nesta sessão) e o registro real da tarefa. Esses ficam para a validação do dono (HT-15) e o T86.
- Testes do backend/frontend: nada de aplicação foi alterado; `pytest`/`ruff`/`npm` não foram rodados.

## 7. Decisões/propostas (para o fechamento de lote)

- **P-T82-1:** o front (T83) deve considerar offline `online:false` **ou** `heartbeat` > ~25 min.
- **P-T82-2:** a URL quick tunnel muda a cada reinício do cloudflared; o front lê sempre `api.json` da branch `snapshot` antes de chamar a API (já previsto em DEC-57).
- **P-T82-3:** o commit orfão usa `commit-tree` em vez de `checkout --orphan` (mesmo resultado, sem trocar de branch no clone nem depender da versão do git).
