# Aviso de legendas IA em rascunho na tela de relatório (BL-38, frontend)

## O que mudou
A emissão é disparada em `components/relatorio/emissao-versoes.tsx` (renderizado por `app/inspecoes/relatorio/page.tsx`, que não precisou de alteração); o tratamento ficou no componente.
- `03_frontend/lib/types.ts:511-512`: `RelatorioEmitido.fotos_ia_em_rascunho?: UUID[]` (opcional: ausente em respostas antigas).
- `03_frontend/components/relatorio/emissao-versoes.tsx:45` estado `fotosRascunho`; `:72-74` zera antes da emissão e grava `nova.fotos_ia_em_rascunho?.length ?? 0`; `:135-144` `<Alert variant="warning">` (estilo já usado no app, não bloqueante): «N foto(s) com legenda IA ainda em rascunho; só legendas aprovadas aparecem no relatório.». Vazio/ausente: nada é exibido.
- Backend não alterado.

## Comandos (a partir de 03_frontend/)
- `npm ci` (node_modules não existia no worktree)
- `npm run lint` → `✔ No ESLint warnings or errors`
- `npm run build` → build concluído; `/inspecoes/relatorio` gerada.

## Não testado
Não abri no navegador nem rodei Playwright (e2e); não há teste e2e novo para o aviso. O comportamento visual e a emissão real com fotos em rascunho não foram verificados.
