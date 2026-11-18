# E2E offline online-first (DEC-26) — T78

**Status: EXECUTADA (retomada na T101) — 2 cenários, 2 passaram (Chromium, build de produção).**

Histórico: a T78 original foi marcada `done` sem executar, pois a branch não continha o Service Worker da T77 (`sw.js`, `offline.html`). Com o SW em `main` (DEC-26, DEC-56), o spec foi escrito e rodado.

## Entregáveis

- `03_frontend/e2e/offline-dec26.spec.ts` — os dois cenários.
- `03_frontend/playwright.offline.config.ts` — config separado (`playwright.config.ts` não foi alterado). O `webServer` roda `npm run build && node e2e/servir-out.mjs` com `NEXT_PUBLIC_API_URL=http://api.e2e.test:8000/api/v1`, `NEXT_PUBLIC_API_DISCOVERY_URL=""` (descoberta desligada, para a falha de rede virar erro explícito e não modo leitura) e `NEXT_PUBLIC_BASE_PATH=""`.
- `03_frontend/e2e/servir-out.mjs` — servidor estático Node puro para `out/`.
- Execução (a partir de `03_frontend/`): `npx playwright test -c playwright.offline.config.ts`.

**Desvio do pedido:** a tarefa pedia `npm run start`, mas o app usa `output: "export"` (`next.config.mjs`) e `next start` não serve o export estático. Usa-se `servir-out.mjs` no lugar (mesma abordagem do `sw-basepath.spec.ts`).

## Cenários

1. **Leitura offline.** Online, carrega `GET /sistemas-prediais` e `GET /contratos` (com `Authorization`) e confere que ficaram no cache do SW. Com `context.setOffline(true)`, as duas leituras seguem respondendo do cache dentro do TTL (mesmo com a "rede" mockada devolvendo outra versão). `GET /edificacoes` (fora da allowlist) falha com erro de rede. A navegação para `/edificacoes/` cai no `offline.html` (título "Sem conexão", "Você está sem conexão").
2. **Escrita offline.** Em `/edificacoes/`, preenche "Nova edificação", corta a rede e envia: o diálogo continua aberto com o alerta de erro "Falha de conexão / Não foi possível conectar ao servidor". Verificado: nenhum POST chegou ao mock; `indexedDB.databases()` vazio; `localStorage` sem chave de fila (`fila|queue|pend|outbox|sync`) e sem o dado digitado; nenhum request não-GET nem de `/edificacoes` nos caches (`caches`). Ao reconectar, 1,5 s depois nada é reenviado.

## O que foi mockado

Toda a API, via `context.route` (necessário para o SW enxergar as requisições): `/auth/me` (auditor), `GET /sistemas-prediais` e `GET /contratos` (corpo `{versao, rota}`), `GET /edificacoes` (lista vazia), `POST /edificacoes` (contador). Com a rede "cortada" o mock aborta (`internetdisconnected`) além do `setOffline(true)`. O token é falso, em `localStorage`. **Não foi testado contra o backend real**, então o formato real das respostas e a UI com dados reais não foram exercitados.

## Resultado da execução

- `npx playwright test -c playwright.offline.config.ts`: **2 passed** (≈10 s), Chromium, incluindo o `npm run build` de produção feito pelo `webServer`.
- `npm run lint`: sem avisos nem erros. `npx tsc --noEmit`: sem erros.
- Backend/pytest não aplicável (só frontend alterado; nenhum PostgreSQL usado).

## Lacunas / propostas

- O E2E offline não faz parte do `playwright.config.ts` nem de CI; rodar manualmente (ou incluir um job próprio). Proposta: adicionar script `test:e2e:offline` ao `package.json` em tarefa futura.
- A primeira execução em foreground travou o terminal por falta de saída (build longo); em ambientes interativos rodar com `--reporter=list`.
