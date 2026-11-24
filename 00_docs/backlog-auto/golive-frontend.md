# T111 · Go-live: validação do frontend (GitHub Pages + API fixa)

Refs DEC-59. Data: 2026-11-24. Nenhuma alteração de código foi necessária.

## Comandos e resultado (em `03_frontend`)

```bash
npm ci
npm run lint        # ✔ No ESLint warnings or errors
npm run test:unit   # 23 testes, 23 pass, 0 fail
MSYS_NO_PATHCONV=1 NEXT_PUBLIC_API_URL=https://garra-backend.onrender.com/api/v1 \
  NEXT_PUBLIC_BASE_PATH=/garra-engenharia npm run build   # exit 0, 16 páginas estáticas
```

`NEXT_PUBLIC_API_DISCOVERY_URL` ficou indefinida. Build do Next 14.2.35 com `output: "export"`, `out/` gerado.

**Tamanho de `out/`:** 2.847.879 bytes (≈ 3,0 MB). First Load JS compartilhado: 87,5 kB.

## Verificações

- **API fixa / sem modo leitura:** `descobertaConfigurada()` é `false` quando `NEXT_PUBLIC_API_DISCOVERY_URL` está vazia. Então `descobrirApi()` devolve `NEXT_PUBLIC_API_URL` com `descoberta:false`, a checagem de abertura retorna cedo e `api-client` só entra em modo leitura quando `alvo.descoberta` é verdadeiro. A URL `https://garra-backend.onrender.com` está inlinada no chunk 758. As referências a `api.json` no bundle são só o código morto da descoberta.
- **basePath:** o HTML exportado (`out/login/index.html`) referencia `/garra-engenharia/_next/...`, `/garra-engenharia/brand/*.svg`, `/garra-engenharia/icon.svg` e `/garra-engenharia/manifest.json`. Os links internos usam `next/link` (basePath automático). `<Logo>`, o ícone e o manifest usam `withBasePath`.
- **Service worker:** `sw-register.tsx` registra `withBasePath("/sw.js")` com `scope: withBasePath("/")`, e o bundle contém o prefixo `/garra-engenharia`. `public/sw.js` calcula `OFFLINE_URL` relativo a `registration.scope`. `manifest.json` usa `start_url`/`scope`/`icons` relativos (`./`). O e2e de SW em browser real não foi rodado aqui.

## Pendências / observações

- Nenhuma decisão nova proposta.
- O `npm ci` avisa que o script de install do `unrs-resolver` não está coberto por `allowScripts` (só warning).
