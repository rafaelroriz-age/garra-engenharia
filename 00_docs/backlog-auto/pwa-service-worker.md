# PWA — Service Worker de leitura (DEC-26 / ADR-03 / ADR-15)

Implementação do Service Worker online-first. Escritas (visita, ocorrência, foto) **não** são interceptadas: falham com o erro nativo de rede, sem fila local.

## Arquivos

| Arquivo | Papel |
|---|---|
| `03_frontend/public/sw.js` | Service Worker (JS puro, sem dependência nova) |
| `03_frontend/public/offline.html` | Fallback de navegação sem rede (pt-BR, ícone e cores do manifest) |
| `03_frontend/lib/sw-cache.ts` | Regras puras (allowlist, TTL, chave de cache) — **fonte de teste** |
| `03_frontend/lib/sw-cache.test.ts` | Testes (`npm run test:unit`, `node:test`) |
| `03_frontend/components/sw-register.tsx` | Registro (só `NODE_ENV === 'production'` e `'serviceWorker' in navigator`) + limpeza no logout |
| `03_frontend/app/layout.tsx` | Inclui `<SwRegister />` (única alteração) |
| `03_frontend/lib/api-client.ts` | `clearAuthToken()` (ponto único de logout) dispara o evento `garra:clear-sw-cache` |

`app-shell.tsx` não foi tocado; `theme-provider.tsx` e `theme-toggle.tsx` também não.

## Rotas cacheadas (verificadas em `04_backend/app/api/v1/`)

A API é cross-origin (`NEXT_PUBLIC_API_URL`, padrão `http://localhost:8000/api/v1`); a correspondência é feita pelo `pathname`, independente da origem.

| Rota (GET) | Tipo | TTL | Por usuário |
|---|---|---|---|
| `/api/v1/sistemas-prediais` | dados mestre | 24 h | não (sem autenticação na API) |
| `/api/v1/gabarito/tipos-anomalia`, `/tipos-falha`, `/localizacoes` | dados mestre | 24 h | não |
| `/api/v1/contratos` (com query) e `/api/v1/contratos/{id}` | contratos | 5 min | **sim** |

O filtro "em andamento" é parâmetro de query de `/contratos`; como a query faz parte da chave, cada filtro é uma entrada própria.

## Estratégia

- **Stale-while-revalidate** com TTL: entrada dentro do TTL é servida do cache e revalidada em segundo plano. Entrada **vencida nunca é servida** — vai à rede (assim, sem rede, um dado vencido não aparece como se fosse atual). Consequência: o ganho offline real é limitado à janela do TTL; ver limitações.
- Só respostas `200` sem `Cache-Control: no-store|private` são gravadas. Resposta `401/403` apaga a entrada.
- Navegação (`mode: navigate`) sem rede → `/offline.html`, pré-cacheado no `install`.
- Não-GET: `return` sem `respondWith` (não interceptado).

### Escolha para dados dependentes de token (contratos)

Contratos exigem `Authorization: Bearer`. Escolhido: (1) TTL curto de 5 min; (2) a chave de cache inclui um fingerprint SHA-256 (8 bytes) do cabeçalho `Authorization` (nunca o token), de modo que outro usuário no mesmo navegador não recebe resposta alheia; sem `Authorization` não se cacheia; (3) no logout, `clearAuthToken()` dispara `garra:clear-sw-cache` e `SwRegister` manda `CLEAR_DATA_CACHE` ao SW, que apaga o cache de dados inteiro.

## Versionamento e invalidação

- `CACHE_VERSION = "v1"` em `sw.js` compõe os nomes `garra-sw-data-v1` e `garra-sw-shell-v1`. Mudou formato/regra → incrementar; o `activate` apaga todo cache com prefixo `garra-sw-` que não seja o atual, e faz `clients.claim()`; `install` usa `skipWaiting()`.
- O navegador revalida `/sw.js` em cada navegação; qualquer alteração de byte atualiza o SW.
- Allowlist duplicada em `sw.js` (não importa TS). O teste `public/sw.js duplica exatamente as regras deste módulo` falha se os padrões de `sw.js` divergirem de `lib/sw-cache.ts`.

## O que NÃO é cacheado e por quê

- **Qualquer método ≠ GET** — escritas exigem conectividade (DEC-26).
- **`/auth/*`** — credenciais/identidade do usuário.
- **`/portal/*`** — dados do contratante externo; risco de exposição entre perfis no mesmo dispositivo.
- **Fotos (`/fotos`), downloads, relatórios, documentos, upload** — binários grandes e potencialmente sensíveis (laudos, imagens de edificações de terceiros).
- Qualquer rota fora da allowlist (inspeções, ocorrências, edificações, dashboard…) — dados voláteis ou com escrita frequente.
- Respostas `no-store`/`private`, esquemas não-http(s), respostas não-200.
- Esta lista é aplicada **antes** da allowlist (veto tem precedência).

## Verificação

| Comando (em `03_frontend`) | Resultado |
|---|---|
| `npm run test:unit` | 9/9 testes passam |
| `npm run lint` | sem avisos/erros |
| `npm run build` | sucesso |

Não há runner unitário no projeto (só Playwright e2e). Usei `node --test` (Node 26 executa `.ts` nativamente), sem dependência nova; para isso foi habilitado `allowImportingTsExtensions` em `tsconfig.json` (o teste importa `./sw-cache.ts`) e adicionado o script `test:unit` em `package.json`. O build compila o teste junto (type-check) sem problemas.

**Não testado manualmente em navegador** (sem navegador disponível neste ambiente): registro real do SW, SWR, fallback offline e limpeza no logout foram verificados apenas por leitura de código e pelos testes das regras puras. O fluxo de `sw.js` (eventos `fetch`/`activate`/`message`) não tem teste automatizado. Recomenda-se teste manual com `npm run build && npm start` + DevTools → Application → Service Workers (modo Offline), ou um spec Playwright futuro.

## Limitações conhecidas

- Como entrada vencida não é servida, o uso sem rede só funciona dentro do TTL (5 min para contratos). Isso é intencional (DEC-26: sem offline); se o cliente quiser tolerância maior em dados mestre, basta aumentar `MESTRE_TTL_MS`.
- O fingerprint depende do token: após renovação de token (login novo) o cache de contratos recomeça; entradas antigas expiram pelo TTL ou são apagadas no logout/próximo `activate`.
- Entradas do cache de dados não são removidas ativamente por TTL (só sobrescritas/limpas no logout ou troca de versão); volume é pequeno.
- Logout em outra aba/dispositivo não dispara a limpeza nesta aba; o TTL de 5 min limita a exposição. Expiração do token sem logout explícito idem.
- Em desenvolvimento (`next dev`) o SW não é registrado.
- `sw.js` carrega `/offline.html` no `install`; se esse fetch falhar, a instalação do SW falha (o app segue funcionando sem SW).
- O SW é servido em `/sw.js` com escopo `/`; se houver proxy/CDN com cache agressivo, deve-se evitar cachear `/sw.js`.

## Decisões propostas (não aplicadas aos documentos de gestão)

1. Registrar em `decisoes.md`, como detalhamento de DEC-26: contratos em cache com TTL de 5 min, chave por fingerprint do token e limpeza no logout; dados mestre com TTL 24 h.
2. Adotar `node --test` como runner de testes unitários do frontend para lógica pura (alternativa: Vitest, a decidir se crescer a necessidade de testes de componente).
3. Considerar spec Playwright (`e2e/`) para validar SW em build de produção, no fechamento de lote.
