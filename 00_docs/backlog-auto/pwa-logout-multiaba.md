# PWA: logout limpa o cache do Service Worker em todas as abas (DEC-56)

## Mecanismo
- Evento `storage` do `localStorage` (dispara nas *demais* abas do mesmo origin quando a chave do token `garra:access_token` é removida ou o storage é limpo). Não usa BroadcastChannel, logo não há caminho/basePath envolvido (DEC-55).
- Decisão em função pura `isLogoutStorageEvent(ev, tokenKey)` (`03_frontend/lib/sw-cache.ts`): `key===token && newValue===null` ou `key===null && newValue===null` → limpa; outra chave ou token trocado por outro → ignora.
- `components/sw-register.tsx` registra o ouvinte `storage` dentro do mesmo `useEffect` (uma vez; cleanup remove ambos os listeners) e reaproveita `limpar()` (`postMessage CLEAR_DATA_CACHE`), sem duplicar lógica. Allowlist, TTLs e o que é cacheado não mudaram. `AUTH_TOKEN_STORAGE_KEY` passou a ser exportada de `lib/api-client.ts`.
- Sem erro quando não há SW/`controller` (`?.`), em SSR (efeito só no cliente, e só em produção com `serviceWorker`) ou com evento ausente (função pura devolve `false`).

## Limitações
- Aba fechada no momento do logout não recebe o evento; o TTL (contratos 5 min, por usuário via fingerprint do token) limita a exposição.
- Navegador sem `serviceWorker`/`localStorage` não tem cache a limpar.
- Se outra aba nunca é controlada pelo SW (`controller` nulo, ex. 1º carregamento), nada é limpo.
- Playwright não executado (opcional).

## Comandos (03_frontend)
- `npm run test:unit`: tests 23, pass 23, fail 0 (5 novos em `lib/sw-cache.test.ts`).
- `npm run lint`: No ESLint warnings or errors.
- `npm run build`: sucesso, todas as rotas estáticas.
