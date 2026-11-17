# T79 · Runtime local de produção no PC sem Docker (DEC-57)

- Tarefa: T79 (papel devops), Bloco G do `BACKLOG.md`. Decisão de origem: DEC-57 (P1).
- Data: 2026-11-17. Branch: `worktree-backlog-T79`.
- Entregas: `05_infra/local/garra-local.ps1`, `05_infra/local/.env.example`, entradas novas no `.gitignore`.
- Resultado: `setup`, `start`, `status`, `backup` e `stop` rodaram de verdade neste PC (Windows 11 Pro 10.0.26200, Windows PowerShell 5.1.26100.9818), com exit 0. As saídas estão na §5.

## 1. Arquitetura

```text
PC do dono (Windows, sem Docker)
│
├─ <repo>\05_infra\local\                    (no OneDrive; versionado: só o .ps1 e o .env.example)
│   ├─ garra-local.ps1                       setup|start|stop|status|backup
│   ├─ .env            [git-ignorado]        segredos e configuração do runtime
│   ├─ bin\pgsql\      [git-ignorado]        PostgreSQL 16.16 portátil (zip EDB, 137 MB após limpar pgAdmin/doc)
│   ├─ storage\        [git-ignorado]        STORAGE_LOCAL_DIR (arquivos do T80)
│   ├─ backups\        [git-ignorado]        garra-AAAAMMDD-HHmm.dump (pg_dump -Fc), retenção 14
│   ├─ logs\           [git-ignorado]        garra-local.log, postgres.log, uvicorn-*.out/err.log
│   └─ run\            [git-ignorado]        uvicorn.pid; diretório de trabalho de alembic/seeds/uvicorn
│
├─ <repo>\04_backend\.venv-prod\ [git-ignorado]  Python 3.12 + requirements.txt (222 MB)
│
└─ %LOCALAPPDATA%\garra\                     (fora do OneDrive)
    ├─ pgdata\                               cluster PostgreSQL (porta 5434, scram-sha-256, ICU pt-BR)
    ├─ pgsql\  (junção → <repo>\05_infra\local\bin\pgsql)   caminho ASCII para executar o Postgres
    └─ msys64\                               MSYS2 portátil só com Pango (UCRT64) para o WeasyPrint (774 MB)

Processos: postgres.exe (pg_ctl, porta 5434, só localhost)
           python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 (sem --reload)
```

Como o backend recebe a configuração: o script lê `05_infra/local/.env` e exporta cada chave como variável de ambiente do próprio processo, mais `PYTHONPATH=<repo>\04_backend`, `PYTHONUTF8=1` e `PGPASSWORD`. Alembic, seeds e uvicorn herdam esse ambiente e rodam com o diretório de trabalho em `05_infra/local/run/`. Assim o `04_backend/.env` de desenvolvimento nunca é lido: o `Settings` do pydantic usa `env_file=".env"` relativo ao diretório de trabalho (`04_backend/app/core/config.py:18`), e em `run/` não há `.env`. O `alembic.ini` resolve as migrations por `%(here)s/alembic`, então `-c <repo>\04_backend\alembic.ini` funciona de qualquer diretório.

## 2. Comandos

A partir da raiz do repositório:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 setup
powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 start
powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 status
powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 backup
powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 stop
```

Opções: `setup -PularPango` (não instala o MSYS2; o PDF fica indisponível e o DOCX continua funcionando) e `start -PularSeeds`. Sem argumento, o script mostra o uso.

| Subcomando | O que faz |
|---|---|
| `setup` | (1) Cria `.env` a partir do `.env.example` se faltar. Preenche `POSTGRES_PASSWORD` (48 hex), `JWT_SECRET_KEY` (96 hex) e `ADMIN_SENHA` (24 hex) **só se estiverem vazias**, acrescenta chaves novas do exemplo que faltarem e nunca troca um valor existente. `SNAPSHOT_SENHA` fica vazia e o script avisa (HT-14). (2) Baixa `postgresql-<PG_VERSION>-1-windows-x64-binaries.zip` da EDB para `bin\pgsql`, o que é pulado se o diretório já existir. Remove `pgAdmin 4`, `doc`, `symbols` e `StackBuilder` e cria a junção ASCII. (3) Roda `initdb -U garra --pwfile <tmp> -A scram-sha-256 -E UTF8 --locale-provider=icu --icu-locale=pt-BR --locale=pt-BR` em `%LOCALAPPDATA%\garra\pgdata`, pulado se o cluster já existir, e acrescenta ao `postgresql.conf` `port`, `listen_addresses='localhost'`, `password_encryption` e `timezone`. (4) Sobe o Postgres temporariamente e cria `garra_producao` se não existir. (5) Cria `04_backend\.venv-prod` com Python 3.12 (procura `py -3.12`, depois `%LOCALAPPDATA%\Programs\Python\Python312`, depois `uv`) e instala `requirements.txt`. (6) Instala o Pango, se não houver, e testa o WeasyPrint gerando um PDF. |
| `start` | Recusa subir se a porta do uvicorn já estiver com outro processo (antes de migrations e seeds). Roda `pg_ctl start -w` se o Postgres estiver parado, espera `pg_isready`, `alembic upgrade head` e `alembic current`, os seeds (§4) e o uvicorn em 2º plano. Grava o PID em `run\uvicorn.pid` e espera até 90 s o `/health` responder **pelo processo do runtime** (confere que quem escuta a porta é o PID gravado ou um filho dele). |
| `stop` | `taskkill /PID <pid> /T /F` (árvore: o `python.exe` do venv é um lançador que cria o Python real como filho) e `pg_ctl stop -m fast -w`. |
| `status` | Estado do Postgres (`pg_ctl status`), do uvicorn (PID vivo) e `GET http://127.0.0.1:<porta>/health`. Se a porta responder, mas for de outro processo, diz isso em vez de mostrar o JSON. |
| `backup` | Exige o Postgres no ar. Roda `pg_dump -Fc` para `backups\garra-AAAAMMDD-HHmm.dump.parcial`, recusa arquivo vazio, valida com `pg_restore --list`, renomeia para `.dump` e só então apaga os `garra-*.dump` além dos `BACKUP_RETENCAO` mais recentes (ordem por nome). Nunca apaga o último backup bom por causa de uma execução que falhou. |

Toda ação vai para `05_infra/local/logs/garra-local.log` com data, nível e a saída dos programas (prefixo `    |`). Segredos que aparecem em linhas de comando são trocados por `***`.

## 3. Variáveis (`05_infra/local/.env.example`)

| Variável | Padrão | Observação |
|---|---|---|
| `ENVIRONMENT` | `production` | Liga as travas fail-closed do `config.py` (JWT ≥ 32, CORS sem `*`, DeepSeek exige chave). |
| `BACKEND_CORS_ORIGINS` | `https://rafaelroriz-age.github.io,http://localhost:3000` | Pages público (DEC-57 P3) e front local. |
| `RUN_MIGRATIONS_ON_STARTUP` | `false` | O script roda `alembic upgrade head` antes do uvicorn. |
| `POSTGRES_USER` / `POSTGRES_DB` / `POSTGRES_HOST` / `POSTGRES_PORT` | `garra` / `garra_producao` / `localhost` / `5434` | `garra` é o superusuário do cluster dedicado. |
| `POSTGRES_PASSWORD` | gerada | Só hexadecimal, porque entra sem escape na URL do SQLAlchemy (`config.py`, `database_url`). |
| `PG_VERSION` | `16.16` | Última 16.x publicada pela EDB em 2026-11-17 (16.17 a 16.20 respondem 403). |
| `JWT_SECRET_KEY` | gerada | 96 caracteres hex. |
| `JWT_ALGORITHM` / `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `HS256` / `60` | |
| `STORAGE_PROVEDOR` | `local` | Consumida pelo T80. Hoje o `config.py` da `main` ainda não a lê (`extra="ignore"`). |
| `STORAGE_LOCAL_DIR` | vazio → `<repo>\05_infra\local\storage` absoluto | Criada no `start`. |
| `PUBLIC_BASE_URL` | vazio | T80/T82 (URL do túnel). |
| `ADMIN_EMAIL` / `ADMIN_NOME` / `ADMIN_SENHA` | `admin@garra-engenharia.com.br` / `Administrador` / gerada | Usadas pelo `seed_admin`. Sem isso o seed usaria a senha padrão do código (`Admin@Garra123`). |
| `SNAPSHOT_SENHA` | vazia | O dono define (≥ 16 caracteres, HT-14). Consumida pelo T81. |
| `LEGENDA_IA_PROVEDOR` / `DEEPSEEK_API_KEY` | `fake` / vazia | Com `deepseek` em produção a chave é obrigatória. |
| `WEASYPRINT_DLL_DIRECTORIES` | vazio → detectado | O script procura `libpango-1.0-0.dll` em `%LOCALAPPDATA%\garra\msys64\ucrt64\bin`, `C:\msys64\ucrt64\bin` e `C:\msys64\mingw64\bin`. |
| `UVICORN_HOST` / `UVICORN_PORT` | `127.0.0.1` / `8000` | Só localhost: a exposição será pelo túnel do T82. |
| `BACKUP_RETENCAO` | `14` | |

`.gitignore`: o padrão `.env` (linha 2) já cobre `05_infra/local/.env`, conferido com `git check-ignore -v`. Foram acrescentados `05_infra/local/bin/`, `backups/`, `storage/`, `logs/`, `run/` e `04_backend/.venv-prod/`; o `.venv/` existente não cobria `.venv-prod/`. Conferência:

```text
$ git check-ignore -v .env bin/pgsql/bin/pg_ctl.exe backups/x.dump storage/a logs/garra-local.log run/uvicorn.pid ../../04_backend/.venv-prod/pyvenv.cfg
.gitignore:2:.env	.env
.gitignore:49:05_infra/local/bin/	bin/pgsql/bin/pg_ctl.exe
.gitignore:50:05_infra/local/backups/	backups/x.dump
.gitignore:51:05_infra/local/storage/	storage/a
.gitignore:52:05_infra/local/logs/	logs/garra-local.log
.gitignore:53:05_infra/local/run/	run/uvicorn.pid
.gitignore:54:04_backend/.venv-prod/	../../04_backend/.venv-prod/pyvenv.cfg
$ git check-ignore .env.example garra-local.ps1   → nada (versionáveis)
```

## 4. Seeds: quais rodam e por quê

A ordem é a do CI (`.github/workflows/ci.yml`, passo "Aplicar migrations e seed do gabarito"): `alembic upgrade head`, `seed_gabarito`, `seed_admin`. Acrescentei os seeds idempotentes da legenda IA documentados em `05_infra/README.md`.

| Script | Idempotente? | No `start`? |
|---|---|---|
| `seed_gabarito` | Sim (confere por `nome` antes de inserir) | Sim |
| `seed_admin` | Sim ("já existe — nada a fazer") | Sim, com `ADMIN_*` do `.env` |
| `seed_prompt_legenda` | Sim (compara SHA-256 da versão ativa) | Sim |
| `ingerir_conhecimento_ia` | Sim (`ON CONFLICT DO NOTHING`), mas relê todo `00_docs/convertidos` | Só quando `trechos_conhecimento_ia` está vazia |
| `seed_demo` | Sim, mas cria dados `DEMO` e usa storage | **Não** (é dado de demonstração) |
| `seed_benchmark_rfo` | Só com `--reset` | **Não** (é benchmark) |

## 5. Execução real neste PC (2026-11-17)

Comandos rodados a partir de `05_infra/local/` do worktree, com `& "$PSHOME\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File .\garra-local.ps1 <cmd>`.

### 5.1 `setup`: 1ª tentativa falhou (corrigida)

```text
17:05:13 [INFO] Baixando https://get.enterprisedb.com/postgresql/postgresql-16.16-1-windows-x64-binaries.zip
17:05:24 [INFO] Download concluido: 360,6 MB
17:09:28 [INFO] PostgreSQL instalado: postgres (PostgreSQL) 16.16          (extração no OneDrive: ~4 min)
17:09:28 [INFO] exec: initdb.exe -D C:\Users\dynatest\AppData\Local\garra\pgdata -U garra --pwfile ... -A scram-sha-256 -E UTF8 --locale-provider=icu --icu-locale=pt-BR --locale=pt-BR
    | executando pós-inicialização ... FATAL:  sequência de bytes é inválida para codificação "UTF8": 0xc1 0x72
    | initdb: removendo diretório de dados "C:/Users/dynatest/AppData/Local/garra/pgdata"
17:09:33 [ERRO] initdb.exe terminou com codigo 1
```

Causa: `0xc1 0x72` é "Ár" em cp1252, de "Área de Trabalho". No pós-init, o `initdb` passa ao backend caminhos de `share\` derivados do local do executável. Com o binário dentro da pasta com acento, esses bytes cp1252 entram num cluster UTF8 e são rejeitados. Correção: os binários continuam em `05_infra\local\bin\pgsql`, como pedido, mas o script cria a junção `%LOCALAPPDATA%\garra\pgsql` → `bin\pgsql` e executa **todos** os programas do Postgres por ela. Testei antes à mão: `initdb` pela junção deu exit 0, e o cluster de teste foi apagado em seguida.

### 5.2 `setup`: 2ª execução (ok)

```text
17:10:48 [INFO] .env ja existe: so chaves vazias/ausentes serao preenchidas
17:11:03 [INFO] initdb concluido em C:\Users\dynatest\AppData\Local\garra\pgdata (porta 5434, scram-sha-256, ICU pt-BR)
17:11:05 [INFO] Postgres aceitando conexoes na porta 5434
17:11:06 [INFO] Banco garra_producao criado
17:11:09 [INFO] Postgres parado (pg_ctl stop -m fast)
17:11:09 [INFO] Criando venv ...\04_backend\.venv-prod com C:\Users\dynatest\AppData\Local\Programs\Python\Python312\python.exe
17:16:43 [INFO] venv ok (python, fastapi, uvicorn, alembic): 3.12.4 0.163.2 0.54.0 1.20.1
17:16:43 [INFO] Baixando MSYS2 portatil (sem instalador, sem admin): https://repo.msys2.org/distrib/msys2-x86_64-latest.sfx.exe
17:18:49 [INFO] exec: bash.exe -lc "pacman -Syu --noconfirm"            (2x, conforme a doc do MSYS2)
17:20:11 [INFO] exec: bash.exe -lc "pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-pango"
17:25:07 [INFO] Pango instalado em C:\Users\dynatest\AppData\Local\garra\msys64\ucrt64\bin
17:25:16 [INFO] WeasyPrint ok: weasyprint 70.0 gerou PDF
17:25:16 [INFO] === setup concluido ===
```

### 5.3 `setup`: 3ª execução (idempotência, 20 s)

```text
17:25:37 [INFO] POSTGRES_PASSWORD ja definida: mantida
17:25:37 [INFO] JWT_SECRET_KEY ja definida: mantida
17:25:37 [INFO] ADMIN_SENHA ja definida: mantida
17:25:37 [WARN] SNAPSHOT_SENHA vazia: o dono deve definir a senha da equipe (>= 16 caracteres, HT-14)
17:25:37 [INFO] PostgreSQL ja presente em ...\05_infra\local\bin\pgsql: download pulado
17:25:37 [INFO] Cluster ja existe em C:\Users\dynatest\AppData\Local\garra\pgdata: initdb pulado
17:25:40 [INFO] Banco garra_producao ja existe
17:25:41 [INFO] venv ja existe: ...\04_backend\.venv-prod
17:25:53 [INFO] Pango ja presente em C:\Users\dynatest\AppData\Local\garra\msys64\ucrt64\bin
17:25:56 [INFO] WeasyPrint ok: weasyprint 70.0 gerou PDF
17:25:56 [INFO] === setup concluido ===            exit=0
```

### 5.4 `start`: 1ª execução expôs um bug (corrigido)

```text
17:26:17 [INFO] app.scripts.seed_gabarito: Seed do gabarito concluído: {'sistemas_prediais': 15, 'subsistemas': 113, 'tipos_anomalia': 6, 'tipos_falha': 9, 'localizacoes': 47}
17:26:26 [INFO] app.scripts.seed_admin: Usuário auditor 'admin@garra-engenharia.com.br' criado.
17:26:33 [INFO] app.scripts.seed_prompt_legenda: Versão 1 de 'legenda_foto' criada e ativada. (9153 caracteres, sha256=163d581e…)
17:26:40 [INFO] ingerir_conhecimento_ia: Inseridos: 1056; já existentes: 0
17:26:42 [INFO] GET /health -> 200 {... "environment":"development","database":"ok"}
uvicorn-*.err.log: ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)
```

O `/health` que respondeu **não era** o do runtime: a porta 8000 deste PC está com `com.docker.backend.exe` (PID 28008), o backend de desenvolvimento publicado pelo Docker Desktop. O uvicorn do runtime falhou no bind e saiu. Correções no script: `Assert-PortaLivre` no início do `start` (via `Get-NetTCPConnection`), `Test-PortaDoRuntime` antes de aceitar o `/health`, e `status` dizendo de quem é a porta.

### 5.5 `start` com a porta 8000 ocupada (falha esperada) e seeds pela 2ª vez

```text
17:27:57 [INFO] alembic current: c6f2a8d4e1b9 (head)
17:27:59 [INFO] app.scripts.seed_gabarito: Seed do gabarito concluído: {... mesmos totais ...}
17:28:02 [INFO] app.scripts.seed_admin: Usuário 'admin@garra-engenharia.com.br' já existe (id=176ea593-…) — nada a fazer.
17:28:06 [INFO] app.scripts.seed_prompt_legenda: Versão ativa já tem este conteúdo — nada a fazer.
17:28:06 [INFO] ingerir_conhecimento_ia pulado: trechos_conhecimento_ia ja tem 1056 linhas
17:28:15 [ERRO] Porta 8000 ja esta em uso por PID 28008 (com.docker.backend.exe). Libere a porta ou mude UVICORN_PORT no .env.      exit=1
```

Depois disso a checagem passou para antes das migrations. Para não mexer no Docker de dev, o `.env` **local do teste** usou `UVICORN_PORT=8001`; o padrão do `.env.example` continua 8000, como pede a tarefa.

### 5.6 `start` (porta 8001), `status`, `backup`, `stop`, `status`

```text
17:28:45 [INFO] alembic current: c6f2a8d4e1b9 (head)
17:28:57 [INFO] exec (2o plano): python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 1 --proxy-headers --forwarded-allow-ips 127.0.0.1
17:28:57 [INFO] uvicorn iniciado (PID 34604)
17:29:19 [INFO] GET /health -> 200 {"status":"ok", ..., "environment":"production","database":"ok"}
17:29:19 [INFO] === start concluido ===                                                     exit=0

17:29:35 [INFO] status: postgres=no ar (porta 5434, dados C:\Users\dynatest\AppData\Local\garra\pgdata); uvicorn=no ar (PID 34604); GET http://127.0.0.1:8001/health -> 200 {"status":"ok","app":"Sistema de Automação de Relatórios Prediais","environment":"production","database":"ok"}      exit=0

17:29:36 [INFO] exec: pg_dump.exe -h localhost -p 5434 -U garra -d garra_producao -Fc -f "...\backups\garra-20261117-1729.dump.parcial"
17:29:37 [INFO] dump ok: ...\backups\garra-20261117-1729.dump (265,4 KB, 122 itens no indice)
17:29:37 [INFO] retencao: 1 dump(s) mantidos (limite 14)                                     exit=0

Teste de retenção: 15 arquivos fictícios garra-20260101-0001..0015.dump + o real = 16
17:29:48 [INFO] retencao: removido garra-20260101-0002.dump
17:29:48 [INFO] retencao: removido garra-20260101-0001.dump
17:29:48 [INFO] retencao: 14 dump(s) mantidos (limite 14)        (os fictícios foram apagados depois)

17:29:55 [INFO] exec: taskkill.exe /PID 34604 /T /F
17:29:56 [INFO] uvicorn encerrado (PID 34604 e filhos)
17:29:57 [INFO] Postgres parado (pg_ctl stop -m fast)                                         exit=0
17:30:01 [INFO] status: postgres=parado (...); uvicorn=parado; GET http://127.0.0.1:8001/health -> sem resposta    exit=0
Get-NetTCPConnection nas portas 8001 e 5434 em LISTEN: 0
```

O `status` e o `backup` rodaram em processos separados do `start`, o que confirma que o uvicorn sobrevive ao fim do script que o lançou.

### 5.7 Estado deixado no PC

- `%LOCALAPPDATA%\garra\pgdata` (cluster de teste, 72,4 MB, só com seeds) foi **apagado** no fim. Ele foi criado com a senha do `.env` deste worktree, que some com o worktree, e a trava do `setup` (abaixo) bloquearia o setup do dono no checkout principal. O dono roda `setup` de novo no checkout principal, que recria o cluster com o `.env` de lá.
- Ficaram em `%LOCALAPPDATA%\garra\`: `msys64\` (774 MB, Pango pronto; o próximo `setup` o reaproveita e economiza ~8 min) e a junção `pgsql\`, que aponta para o `bin\pgsql` deste worktree. O `setup` no checkout principal detecta o alvo diferente e recria a junção (`Set-PgJuncao`).
- No worktree, tudo git-ignorado: `05_infra/local/{.env,bin,backups,logs,run}` e `04_backend/.venv-prod`.

Trava de segurança acrescentada: se existe cluster em `pgdata` e o `.env` ainda não existe, o `setup` **aborta** em vez de gerar uma senha nova que deixaria o cluster inacessível.

## 6. WeasyPrint (PDF) no Windows

- `04_backend/Dockerfile.render` instala via apt `libpango-1.0-0`, `libpangocairo-1.0-0`, `libgdk-pixbuf-2.0-0`, `libcairo2`, `libffi-dev` e `shared-mime-info`.
- No Windows o projeto **não resolvia isso até agora**. Vários docs (`ltip-pipeline.md`, `rfo-art-execucao.md`, `benchmark-pos-t28.md`) registram `OSError: cannot load library 'libpango-1.0-0'` e testes de PDF pulados, com o PDF exercitado só em container.
- Solução no `setup`: MSYS2 portátil (`msys2-x86_64-latest.sfx.exe -y -o…`, sem instalador e sem admin) em `%LOCALAPPDATA%\garra\msys64`, mais `pacman -S mingw-w64-ucrt-x86_64-pango`. O `start` exporta `WEASYPRINT_DLL_DIRECTORIES=…\msys64\ucrt64\bin`. Verificado: `weasyprint 70.0 gerou PDF` com o `.venv-prod`.
- Fica fora do OneDrive e num caminho ASCII pelo mesmo motivo do pgdata: são milhares de arquivos pequenos, e o MSYS2 não lida bem com caminhos que tenham espaço e acento.

## 7. Testes do projeto (checklist do PR)

- Nenhum arquivo de `04_backend/` ou `03_frontend/` foi alterado (só `05_infra/local/`, `.gitignore` e este doc). Por isso `pytest`, `ruff check .`, `npm run lint` e `npm run build` **não foram rodados**: não há código Python nem TS novo para eles.
- Validação do que foi criado: parser do PowerShell 5.1 (`[Management.Automation.Language.Parser]::ParseFile`) com 0 erros; o script inteiro é ASCII (`file garra-local.ps1` → `ASCII text`), para o PS 5.1 não corromper acentos em `.ps1` sem BOM; execução real dos cinco subcomandos (§5).
- Não há teste automatizado do `.ps1` (Pester não foi usado). Proposta abaixo.

## 8. Limitações e riscos

1. **Porta 8000 × Docker de dev**: neste PC o Docker Desktop publica a 8000 (backend de dev). Com os dois no ar, o `start` recusa subir e diz por quê. O dono escolhe: parar o compose de dev ou definir outra `UVICORN_PORT` no `.env` (o T82 deve ler a mesma variável para o túnel).
2. **`stop` não é gracioso para o uvicorn**: no Windows não há SIGTERM e a árvore é encerrada com `taskkill /T /F`. Requisições em andamento são cortadas. O Postgres para com `-m fast`, que é limpo.
3. **OneDrive**: `bin\pgsql` (137 MB) e `.venv-prod` (222 MB) ficam dentro da pasta sincronizada, porque a tarefa pede esses caminhos. O OneDrive vai enviá-los, e há relato anterior de `OSError: [Errno 22]` ao ler arquivo de venv no OneDrive (`ltip-pipeline.md`, linha 84); aqui não aconteceu. A extração do zip no OneDrive levou ~4 min. Os dumps em `backups\` sincronizarem é desejado (DEC-57: "dumps sincronizados pelo OneDrive").
4. **Download sem verificação de integridade**: a EDB não publica um SHA-256 simples para o zip e o script não confere hash. O download é por HTTPS (TLS 1.2 forçado).
5. **PID reaproveitado**: `Get-UvicornPid` só confere se o PID do arquivo está vivo. Se o Windows reaproveitar o número depois de um crash, `status`/`stop` podem enxergar outro processo. O `start` mitiga com a checagem de porta.
6. **Dois backups no mesmo minuto** geram o mesmo nome e o segundo substitui o primeiro (visto no teste de retenção). Com dump diário não há impacto.
7. **`ingerir_conhecimento_ia`** só roda com a tabela vazia. Documentos novos em `00_docs/convertidos` exigem rodar o script à mão (ver `05_infra/README.md`).
8. **`STORAGE_PROVEDOR`/`STORAGE_LOCAL_DIR`/`PUBLIC_BASE_URL`/`SNAPSHOT_SENHA`** já são exportadas, mas o backend da `main` ainda não as lê. Passam a valer com T80/T81.
9. A tarefa agendada no logon, o `git pull` e o túnel são do T82, fora deste escopo.

## 9. Propostas (para o fechamento de lote; não aplicadas em `decisoes.md`)

- **Proposta DEC-57 (complemento P1)**: "Os binários do PostgreSQL ficam em `05_infra/local/bin/pgsql`, mas são executados pela junção ASCII `%LOCALAPPDATA%\garra\pgsql`, porque o `initdb` falha em cluster UTF8 com caminho de instalação acentuado. O Pango do WeasyPrint vem de um MSYS2 portátil em `%LOCALAPPDATA%\garra\msys64`, via `WEASYPRINT_DLL_DIRECTORIES`." Alternativa a avaliar: baixar o PostgreSQL direto em `%LOCALAPPDATA%\garra\pgsql`. Isso eliminaria a junção e tiraria 137 MB do OneDrive, mas muda o caminho pedido no Pronto do T79.
- **Proposta para o T82**: o agente de inicialização deve chamar `garra-local.ps1 start` e ler `UVICORN_PORT` do mesmo `.env` para o `cloudflared tunnel --url`. Antes, deve tratar o código de saída 1 por porta ocupada.
- **Proposta para o T85**: documentar no `05_infra/README.md` a seção "Runtime local de produção (DEC-57)" com a §2 deste doc e o aviso da porta 8000.
- **Proposta de teste**: um teste Pester mínimo para `Set-EnvSeVazio` (não sobrescrever valor existente) e para a retenção do `backup`, com arquivos fictícios.
