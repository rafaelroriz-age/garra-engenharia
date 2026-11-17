# T86: E2E do modo leitura com snapshot cifrado (DEC-57)

Spec Playwright que prova o ciclo completo: online pelo `api.json`, depois PC "desligado" com `snapshot.enc` gerado por `gerar_snapshot`.

## 1. Arquivos

| Caminho | Papel |
|---|---|
| `03_frontend/e2e/modo-leitura-dec57.spec.ts` | O spec (1 teste serial, 3 etapas). Faz o `npm run build` com `NEXT_PUBLIC_BASE_PATH=/garra-engenharia` e `NEXT_PUBLIC_API_DISCOVERY_URL=http://localhost:3100/dados/api.json`, sobe um servidor estático em `node:http` e escreve `api.json`/`snapshot.enc` num diretório temporário. |
| `03_frontend/playwright.modo-leitura.config.ts` | Config próprio (`testMatch` só desse spec, `baseURL` `http://localhost:3100/garra-engenharia/`). `playwright.config.ts` e os outros specs não foram alterados. |

O servidor estático vive dentro do spec (não em `webServer`) porque o teste precisa mudar `api.json` no meio do caminho. Reuso dos helpers existentes: `registrarUsuario` e `criarResponsavel` (`helpers.ts`). O login e a criação de edificação/contrato/ocorrência pela UI seguem o fluxo de `inspecao-helpers.ts`, com URLs relativas (`goto("login/")`) porque `goto("/login")` sairia do basePath.

## 2. O que o teste prova

1. **api.json online** (`api_base` do backend local, heartbeat novo): login pela UI, edificação, contrato LTIP e uma ocorrência criada pela UI (POST 201). Sem faixa de modo leitura.
2. **Snapshot depois da criação**: roda `python -m app.scripts.gerar_snapshot --saida <tmp>/snapshot.enc` (com `SNAPSHOT_SENHA` de teste) e troca o `api.json` para `{"online": false}`. Ao recarregar a tela de ocorrências: aparece a faixa "Modo leitura — dados de …", o diálogo pede a senha, a senha errada dá "Senha incorreta.", a certa abre, a ocorrência recém-criada aparece na lista e "Nova ocorrência", "Editar" e "Excluir" estão desabilitados.
3. **Escrita forçada**: chama o `onClick` do botão Excluir pelas props do React e confirma o `window.confirm`. A tela mostra o alerta "Servidor desligado — modo leitura" e a ocorrência continua na lista. Observação: remover o atributo `disabled` do DOM não basta, porque o React ignora cliques quando a prop `disabled` é true; por isso o teste usa o `onClick` das props.

Nenhum bug real foi achado em `modo-leitura.ts` nem em `api-descoberta.ts`; nada do código de produção foi alterado.

## 3. Como rodar

```powershell
# 05_infra: Postgres no ar (localhost:5433). Banco de teste dedicado, com migrations, admin e gabarito:
cd 04_backend
$env:POSTGRES_PORT='5433'; $env:POSTGRES_DB='garra_e2e_t86'   # + POSTGRES_USER/PASSWORD/HOST e JWT_SECRET_KEY como no .env
python -m alembic upgrade head; python -m app.scripts.seed_admin; python -m app.scripts.seed_gabarito
$env:BACKEND_CORS_ORIGINS='http://localhost:3100'; $env:STORAGE_PROVEDOR='local'
python -m uvicorn app.main:app --port 8010
# em outro terminal, com as mesmas variáveis POSTGRES_*:
cd 03_frontend
$env:E2E_API_BASE_URL='http://localhost:8010/api/v1'
npx playwright test -c playwright.modo-leitura.config.ts
# E2E_ML_SEM_BUILD=1 reaproveita o out/ já construído com as variáveis acima.
```

Atenção: o spec sobrescreve `03_frontend/out/` com o build de teste (basePath de produção e URL de descoberta local). Rode `npm run build` normal depois, se for usar `out/` para outra coisa.

## 4. Saída real

Execução final (build incluído em execuções anteriores; esta com `E2E_ML_SEM_BUILD=1`):

```text
gerar_snapshot:
Snapshot gravado em ...\garra-e2e-ml-e7rQwj\snapshot.enc: 103 rotas, 22507 bytes, sha256 a25dc0e04f28…

  ok 1 [chromium] › e2e\modo-leitura-dec57.spec.ts:128:7 › Modo leitura com snapshot (DEC-57) › online, depois PC desligado: leitura do snapshot com gravação bloqueada (30.5s)

  1 passed (33.3s)
```

`npm run lint`: sem avisos. `npm run build`: verde. `npx tsc --noEmit`: sem erros.

## 5. Ambiente e ressalvas

- Sem Docker neste PC. O Postgres de `05_infra` (localhost:5433) já estava no ar. O banco `garra_engenharia` de dev está com a migration `uq_relatorios_inspecao_tipo_versao` bloqueada por dado duplicado (`inspecao_id=22db6dc2…`, versão `BENCH-01`), então `alembic upgrade head` falha nele. Não mexi nesse dado. Criei o banco `garra_e2e_t86` no mesmo servidor (migrations, `seed_admin` e `seed_gabarito` aplicados); ele pode ser descartado com `DROP DATABASE garra_e2e_t86`.
- A porta 8000 estava ocupada por outro processo (backend de outra sessão); o backend do teste usou a 8010 (`E2E_API_BASE_URL`).
- Dependências Python instaladas com `python -m pip` (o `pip` do PATH é o do Python 3.14); `pillow>=10.3,<11` do `requirements.txt` não compila no Python 3.12 local, usei o Pillow atual. Só ambiente local, sem mudança no repositório.
- Os specs antigos não foram rodados nesta tarefa.
- O rótulo do link do contrato é "Ocorrências" (não "Ocorrências (RF-04)", que `inspecao-helpers.ts` ainda usa); vale conferir se `ltip`/`visitas-ocorrencias` ainda passam. Fora do escopo desta tarefa.
