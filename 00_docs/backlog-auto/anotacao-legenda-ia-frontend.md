# Anotação de foto integrada à legenda por IA — frontend (BL-39)

- **Requisitos:** RF-15, RN-16, RN-17; DEC-42 (aprovação só do auditor; editar legenda aprovada invalida).
- **Branch:** `worktree-backlog-T38` (sem push). Commit `feat(frontend): ... (BL-39)`, `Refs BL-39`.
- **Tocado:** `03_frontend/components/photo-annotation-editor.tsx`, `03_frontend/components/foto-upload.tsx`, `03_frontend/e2e/anotacao-legenda-ia.spec.ts` (novo), este doc. Sem `api-client.ts`, `types.ts`, `use-usuario-atual.ts`, `legenda-ia-painel.tsx`. Sem env nem dependências novas.

## 1. Pré-requisito
O worktree estava em `14ead2f`, 180 commits atrás de `main` (sem `legenda-ia-painel.tsx`, T26/T33/T34). Feito `git merge --ff-only main` (fast-forward, sem commit de merge) para `9dd8b9b`.

## 2. Comportamento
- **Novo botão «Anotar foto»** em cada card de foto com `url_publica`: abre o editor existente (`PhotoAnnotationEditor`) com a imagem da foto. Não há fluxo paralelo.
- **Editor com `legendaContexto`** (só ao anotar foto existente): mostra selo («Legenda IA aprovada» / «Legenda IA pendente de aprovação»), campo «Legenda da foto» editável e, se a legenda aprovada for alterada, aviso de que a aprovação será desfeita. **Não há botão de aprovar** (nem para auditor): o texto orienta a usar o painel «Legenda com IA». Para auxiliar, mostra «A aprovação da legenda é feita pelo auditor responsável…» (via `useUsuarioAtual`).
- **Ao salvar:** se a legenda mudou, `PUT /fotos/{id}` `{ legenda }` (sem `aprovar_legenda_ia`). O aviso «voltou a pendente» só aparece se a **resposta do backend** trouxer `rascunho` para uma foto que estava `aprovada` (nada presumido). O card passa a mostrar «Legenda IA: aprovada / pendente de aprovação» (equipe).
- A imagem anotada é enviada (`POST /fotos/upload`) e vinculada como **nova foto** (`POST …/fotos`, legenda = texto do campo, sem estado de IA). A original e sua legenda IA ficam intactas.

## 3. Lacunas (não editei os arquivos de outras tarefas)
1. **Não existe API para substituir a imagem de uma foto existente:** `FotoUpdatePayload`/`FotoUpdateInput` só têm `legenda`, `ordem`, `aprovar_legenda_ia`. Por isso a anotação gera uma foto nova. A invalidação do T33 só dispara por mudança de `legenda`, não por mudança de imagem. Se o requisito for invalidar quando a *imagem* muda, precisa de backend (ex.: `storage_key` no PUT que zere a aprovação).
2. **CORS/canvas:** anotar foto existente carrega `url_publica` (URL presignada do storage) com `crossOrigin=anonymous`; o bucket precisa devolver CORS, senão `toDataURL` falha (canvas "tainted"). Não verificado contra MinIO real.
3. A foto-cópia anotada fica duplicada ao lado da original (a UI não oferece substituir/remover automaticamente).

## 4. Comandos e saída (a partir de `03_frontend`)
| Comando | Resultado |
|---|---|
| `npm ci --no-audit --no-fund` | ok (aviso `install-scripts`) |
| `npm run lint` | `✔ No ESLint warnings or errors` |
| `npm run build` | concluído, tabela de rotas exibida, exit 0 |
| `npx next start -p 3124` + `E2E_BASE_URL=http://localhost:3124 npx playwright test e2e/anotacao-legenda-ia.spec.ts e2e/legenda-ia-aprovacao.spec.ts e2e/legenda-ia.spec.ts` | `10 passed (13.0s)` (1ª rodada: 1 falha por seletor ambíguo no spec novo, corrigido) |

Não rodei `rfo.spec.ts`/`ltip.spec.ts` (exigem backend/banco/MinIO) nem pytest (só frontend tocado).

## 5. Teste manual (cenário básico)
Logar como auditor → visita com foto com legenda IA aprovada → «Anotar foto» → editar legenda → ver aviso → «Salvar marcação» → ver «voltou a pendente» e «Legenda IA: pendente de aprovação» → abrir «Legenda com IA» e aprovar. Como auxiliar: o editor não oferece aprovar. Não executado com backend real; mobile/leitor de tela não verificados.

## 6. Propostas (não registradas em `decisoes.md`)
- Endpoint/campo para substituir a imagem de uma foto mantendo o id, com invalidação da aprovação (fecha a lacuna 1).
- Remover o campo de legenda inline do card para fotos aprovadas (duas portas de edição), como já proposto na T34.
