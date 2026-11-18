# T90 — E2E do Service Worker no export estático com basePath (R-22)

## Arquivos

| Arquivo | Papel |
|---|---|
| `03_frontend/playwright.sw.config.ts` | Config próprio (porta 3110, `baseURL` `http://localhost:3110/garra-engenharia/`); sem `webServer` |
| `03_frontend/e2e/sw-basepath.spec.ts` | Spec: builda com `NEXT_PUBLIC_BASE_PATH=/garra-engenharia` (build de produção, `NODE_ENV=production`), serve `out/` sob o prefixo com servidor estático mínimo em Node e exercita o SW em Chromium real |

Nenhuma dependência nova. Nenhum arquivo de produção (`sw.js`, `sw-register.tsx`) foi alterado: o teste não revelou defeito neles.

Detalhes: a API é mockada com `context.route` (não `page.route`: requisições feitas pelo próprio SW só são vistas por rotas do contexto), com `NEXT_PUBLIC_API_URL=http://api.e2e.test:8000/api/v1` e um token falso em `localStorage`. O mock devolve um campo `versao` que o teste muda entre chamadas: resposta antiga com a "rede" já mudada prova que veio do cache.

## Comandos e saída

```
cd 03_frontend
npm ci                                              # node_modules não existia no worktree (489 pacotes)
npx playwright test -c playwright.sw.config.ts      # build + spec
```

1ª execução (build incluso): `1 failed` — asserção minha errada, não defeito do SW: no stale-while-revalidate a revalidação em segundo plano regrava o cache com o corpo novo, então comparar o corpo depois de uma segunda leitura não prova nada. Removi a asserção (a checagem das chaves do cache já cobre o ponto). Pontos 1–3 e o restante de (4) já passavam.

2ª execução (`E2E_SW_SEM_BUILD=1`, reaproveitando o `out/` já buildado com basePath):

```
  ok 1 [chromium] › e2e\sw-basepath.spec.ts:128:7 › Service Worker sob basePath do Pages (R-22) › registra com scope do basePath, cacheia leitura, limpa no logout e nunca cacheia auth/portal/não-GET (1.5s)
  1 passed (24.9s)
```

`npm run lint`: `✔ No ESLint warnings or errors`. `npm run build`: sucesso (build padrão, sem basePath).

## O que foi provado (Chromium real, build de produção, basePath `/garra-engenharia`)

1. **Registro:** `registration.scope === http://localhost:3110/garra-engenharia/`, `scriptURL` `.../garra-engenharia/sw.js`, SW assume o controle (`clients.claim`) e o `install` pré-cacheou `/garra-engenharia/offline.html` (o `OFFLINE_URL` relativo ao scope de T83 funciona).
2. **Leitura cacheada:** `GET /sistemas-prediais` vai à rede na 1ª vez e, com a "rede" já devolvendo outro corpo, a 2ª vem do cache (dentro do TTL). Idem `GET /contratos` com `Authorization`; sem `Authorization`, contratos não é cacheado (vai à rede).
3. **Logout:** o evento `garra:clear-sw-cache` (o mesmo que `clearAuthToken()` dispara) esvazia o cache `garra-sw-data-v2`; a leitura seguinte volta à rede.
4. **Nunca cacheados:** `GET /auth/me` e `GET /portal/contratos` (com token) buscam a rede toda vez e não aparecem nas chaves do cache; `POST /sistemas-prediais` chega à rede (1 acesso, não interceptado) e não entra no cache.

## Limitações do teste (honestas)

- O logout foi simulado disparando o evento de `clearAuthToken()` + removendo o token, não clicando no botão da UI (o fluxo de UI exigiria mockar toda a API do shell autenticado). A cadeia evento → `SwRegister` → `postMessage(CLEAR_DATA_CACHE)` → SW é a exercitada; `clearAuthToken()` em si (que só remove o token e dispara o evento) continua sem cobertura de navegador.
- Offline "de verdade" (`context.setOffline`) e a navegação para `/offline.html` não foram cobertos (fora dos 4 pontos do critério).
- Só Chromium.

## Estado de R-22

**Resolvido** para o que o risco descrevia: o registro respeita o basePath do Pages e o SW foi exercitado em navegador real (registro, cache de leitura, limpeza no logout, exclusões). Sugestão para o fechamento de lote: mover R-22 para "Resolvido (T90)" em `riscos.md` e anotar as limitações acima como resíduo baixo. Decisão proposta: nenhuma nova.
