# BL-32/BL-33 — E2E do Portal do Cliente (API mockada)

Arquivo: `03_frontend/e2e/portal.spec.ts` (nenhum código de produção alterado; sem novas dependências/variáveis).

## Método
`page.route` intercepta `**/api/v1/*` (`/auth/me`, `/portal/edificacoes`, `/portal/edificacoes/*/acompanhamento|dashboard`, `/portal/relatorios`, `/portal/relatorios/{id}/download/{formato}`). O token é injetado no `localStorage` (`garra:access_token`). Os formatos seguem `lib/types.ts`. Precisa do frontend em `localhost:3000` (a config não sobe `webServer`); nesta execução usei `npm run dev`.

## Cenários (8 testes)
- (a) lista de edificações no seletor, seleção automática da 1ª (`?edificacaoId=`), nav do portal (Acompanhamento / Meus documentos) sem itens do menu global.
- (b) cards Visitas realizadas = 4, Ocorrências = 7, Crítico = 5 (soma do dashboard), contrato, visita, ocorrência e contagem por grau.
- (c) tabela de relatórios; DOCX desabilitado quando `tem_docx=false`; clicar PDF chama `/download/pdf`, abre popup na URL pré-assinada; a chave do storage não aparece na página.
- (d1) vazio: sem edificações e sem documentos. (d2) edificação sem contratos. (d3) 404 no acompanhamento → alerta. (d4) 403 na listagem e no download → alerta.
- (e) perfil `auditor`: o menu global não tem link do portal; acessando `/portal` por URL não há redirecionamento, e a página só mostra o 403 do backend.

## Comandos e resultados (a partir de `03_frontend`)
- `npm ci`; `npx playwright install chromium` (sem erros).
- `npx playwright test e2e/portal.spec.ts` → **8 passed** (~17 s).
- `npm run lint` → sem warnings/erros. `npm run build` → sucesso.
- Backend não tocado; `pytest`/`ruff` não rodados.

## Lacunas (não alteradas, conforme a tarefa)
1. **Sem controle de perfil na UI do portal**: `app/portal/*` e `AppShell` não usam `useUsuarioAtual`; `NavLinks` troca o menu só por `pathname.startsWith("/portal")`. Um `auditor`/`auxiliar` que digita `/portal` vê o menu do portal e o erro 403 do backend. Também não há link do portal no menu global para `cliente` (só se chega por URL) nem redirecionamento pós-login por perfil. A segurança fica no backend (correto), mas a UX é incompleta — sugestão: redirecionar por `role` e expor a entrada.
2. Os specs citados (`legenda-ia`, `foto-origem`, `anotacao-legenda-ia`) não existem neste worktree; usei `ltip.spec.ts` e `helpers.ts` como modelo de estilo.
3. Sem `test.fixme`: nenhum defeito de produção revelado.
4. O download usa `window.open`; o teste valida o popup, não o conteúdo do arquivo (mock).
