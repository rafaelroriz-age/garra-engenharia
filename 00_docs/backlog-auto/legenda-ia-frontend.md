# Painel de legenda por IA com aprovação humana (BL-35, frontend)

- **Tarefa:** T26. BL-35 (RF-15, RN-16, RN-17, DEC-21; contrato de BL-34/DEC-37).
- **Branch:** `worktree-backlog-T26` (sem push). Commit: `feat(frontend): painel de legenda por IA com aprovação humana (BL-35)`, `Refs BL-35`.
- **Tocado:** só `03_frontend/`. Sem backend, sem `app/portal`, sem `components/photo-annotation-editor.tsx` (somente leitura). **Variáveis de ambiente novas:** nenhuma. **Dependências novas:** nenhuma.
- **Documentos de gestão não editados:** `backlog-tarefas.md`, `backlog-kanban.md`, `status.md`, `decisoes.md`, `riscos.md`, `BACKLOG.md`.

---

## 1. Pré-requisito de ordem

| Verificação | Resultado |
|---|---|
| `git log --oneline -1` (início) | `14ead2f` (`backlog: disparo de D03`): a branch **não tinha** BL-34 (`00_docs/backlog-auto/legenda-ia-endpoints.md` ausente; `git log --all` mostrou `ed4b61e feat(backend): endpoints de legenda por IA ... (BL-34)` só em `main`) |
| Ação | `git merge-base --is-ancestor HEAD main` verdadeiro e worktree limpo → `git merge --ff-only main` → `1826f3b` (`backlog: disparo de T26`). Fast-forward, sem commit de merge |

---

## 2. Contrato consumido (só o de `legenda-ia-endpoints.md` §2)

| Chamada (`lib/api-client.ts`) | Requisição | Resposta usada |
|---|---|---|
| `legendaIA.gerar(fotoId, { legenda_bruta })` | `POST /fotos/{foto_id}/legenda-ia/gerar`, corpo `{"legenda_bruta": "<texto>" \| null}` | `FotoRead`: `legenda_ia_sugerida`, `status_validacao_ia`, `alertas_ia`, `pendencias_ia`, `legenda_ia_gerada_em`, `nivel_certeza_ia` (exibido só se vier; hoje o backend não grava) |
| `legendaIA.aprovar(fotoId, legenda)` | `PUT /fotos/{foto_id}`, corpo `{"legenda": "<texto revisado>", "aprovar_legenda_ia": true}` | `FotoRead`: `legenda`, `status_validacao_ia = "aprovada"`, `aprovado_em` |

- O cliente **nunca** envia `aprovado_por_id`, `aprovado_em`, `status_validacao_ia` nem `legenda_ia_sugerida` (o servidor grava pelo token, DP-3).
- `legenda_bruta`: o campo «Anotação de campo (opcional)» vem preenchido com a `legenda_bruta` gravada e é sempre enviado (vazio → `null`, que limpa a gravada, conforme o contrato).
- Limites espelhados do backend: `LEGENDA_MAX_LENGTH = 500` e `LEGENDA_BRUTA_MAX_LENGTH = 5000` (`maxLength` nos `Textarea`).
- Erros: RFC 7807 via `ApiError`/`ApiErrorAlert`. **503** (`legenda-ia-indisponivel`) é trocado por uma mensagem própria («Geração de legenda por IA indisponível… Escreva a legenda manualmente…»), ainda renderizada por `ApiErrorAlert`. 404/422 (`prompt-ia-sem-versao-ativa`, `storage-key-inexistente`, `legenda-ia-sem-sugestao`, `legenda-aprovada-vazia`) mostram título/detalhe vindos da API. O `ApiError` atual não guarda `type`, então o 503 é reconhecido pelo `status`.

Tipos acrescentados em `lib/types.ts`: campos de `LegendaIARead` em `Foto` (todos opcionais), `StatusValidacaoIA`, `NivelCertezaIA`, `LegendaIAGerarInput`, `FotoUpdateInput`, `LEGENDA_MAX_LENGTH`, `LEGENDA_BRUTA_MAX_LENGTH`.

---

## 3. Componentes e integração

| Arquivo | O que mudou |
|---|---|
| `03_frontend/components/legenda-ia-painel.tsx` (novo) | `LegendaIAPainel({ foto, onFotoAtualizada })`: aviso fixo, anotação de campo, botão «Gerar legenda com IA», texto editável, alertas, pendências, «Aprovar legenda» com confirmação em duas etapas |
| `03_frontend/components/foto-upload.tsx` | `useUsuarioAtual()`; botão ícone «Legenda com IA» (Sparkles, `aria-pressed`) em cada card de foto, só para `auditor`/`auxiliar`; o painel da foto selecionada aparece abaixo da grade; `substituirFoto` repassa a `FotoRead` devolvida para `onChange`; o `Input` de legenda do card ganhou `key` com a legenda, para refletir o texto aprovado |
| `03_frontend/lib/api-client.ts` | objeto `legendaIA` (`gerar`, `aprovar`) |
| `03_frontend/lib/types.ts` | tipos da §2 |
| `03_frontend/e2e/legenda-ia.spec.ts` (novo) | 3 testes Playwright com a API mockada (§5) |

Fluxo de upload, colagem (clipboard/Lightshot), editor de anotação, reordenação e remoção: **sem alteração** de lógica (só linhas acrescentadas; ver `git diff 03_frontend/components/foto-upload.tsx`). O painel é inline (não um `Dialog`) porque `FotoUpload` já é renderizado dentro do `Dialog` de `ocorrencia-form-dialog.tsx`.

**Perfil (RN-18/DEC-27):** o painel e o botão só aparecem com `role` `auditor` ou `auxiliar` (mesmo conjunto de `require_equipe` no backend). Enquanto `/auth/me` carrega, ficam ocultos. `cliente` não vê. `app/portal` não usa `FotoUpload` (`grep -rn FotoUpload app components`: só `visita-card.tsx` e `ocorrencia-form-dialog.tsx`). A autorização real continua no backend (403).

---

## 4. Estados da UI

| Estado | Condição | O que aparece |
|---|---|---|
| Oculto | perfil carregando, `cliente` ou nenhuma foto selecionada | nada |
| Sem sugestão | `status_validacao_ia = null` | aviso «A legenda gerada pela IA é sempre um rascunho. Ela só entra no relatório depois que você revisar o texto e aprovar.», anotação de campo, botão «Gerar legenda com IA». Sem campo de sugestão nem botão de aprovar (o backend recusaria com 422 `legenda-ia-sem-sugestao`) |
| Gerando | requisição em curso | botão com spinner e «Gerando legenda...»; campos e botões desabilitados |
| Indisponível (503) | sem provedor de LLM | `ApiErrorAlert` «Geração de legenda por IA indisponível» + orientação para escrever a legenda manualmente |
| Erro (4xx/5xx/rede) | demais falhas | `ApiErrorAlert` com título/detalhe da API |
| Rascunho | `status_validacao_ia = "rascunho"` | badge «Rascunho — aguardando aprovação»; `Textarea` editável com a sugestão (contador `n/500`, data da geração); listas «Alertas da IA» e «Pendências para revisão» quando não vazias; botão «Gerar nova sugestão com IA» |
| Texto vazio | texto só com espaços | «Aprovar legenda» desabilitado, `aria-invalid`, mensagem «Escreva a legenda antes de aprovar.» |
| Confirmando | clique em «Aprovar legenda» | bloco «Confirmar aprovação» com o texto exato que será gravado, «Confirmar aprovação» e «Voltar e revisar». Editar o texto cancela a confirmação. Nada é enviado antes de confirmar |
| Aprovando | `PUT` em curso | spinner «Aprovando...» |
| Aprovada | `status_validacao_ia = "aprovada"` | badge «Aprovada em dd/mm/aa hh:mm»; mensagem `role="status"` «Legenda aprovada. Ela passa a ser usada no relatório.»; a legenda do card mostra o texto aprovado. Pode regenerar (volta a rascunho no backend) ou reaprovar texto editado |

---

## 5. Comandos e saídas

Todos a partir de `03_frontend`. `node_modules` não existia no worktree.

| Comando | Saída |
|---|---|
| `npm ci --no-audit --no-fund` | `added 488 packages in 1m` (aviso de `install-scripts` para `unrs-resolver`, sem erro). `npm audit fix` **não** foi rodado |
| `npm run lint` | `✔ No ESLint warnings or errors` (rodado antes e depois do spec novo) |
| `npx eslint e2e/legenda-ia.spec.ts` | sem saída (ok) |
| `npx tsc --noEmit -p .` | exit 0 |
| `npm run build` | exit 0, `✓ Compiled successfully`, `✓ Generating static pages (10/10)`; `/inspecoes/[id]/visitas` 3.9 kB / 128 kB, `/inspecoes/[id]/ocorrencias` 4.64 kB / 129 kB |
| `npx next start -p 3123` (build acima) + `E2E_BASE_URL=http://localhost:3123 npx playwright test e2e/legenda-ia.spec.ts` | **3 passed (8.4s)**: (1) 503 mostra a mensagem clara e não há «Aprovar legenda»; (2) `auxiliar` gera, vê alertas/pendências, texto vazio desabilita aprovar, confirmação obrigatória, `PUT` com `{"legenda": "<revisado>", "aprovar_legenda_ia": true}`, badge «Aprovada em», legenda do card atualizada; (3) `cliente` não vê o botão. `next start` avisou `"next start" does not work with "output: standalone"`, mas serviu as páginas. Servidor parado em seguida |
| `pytest` / `ruff check .` | não se aplica (backend não tocado) |

O spec novo usa `page.route` para mockar **toda** a API (`/auth/me`, `GET /inspecoes/{id}`, gerar e `PUT`); qualquer rota não mockada responde 404. Não precisa de backend, banco nem provedor. Os specs `rfo.spec.ts`/`ltip.spec.ts` (stack real) **não** foram rodados: `docker` não está disponível neste shell (`docker: command not found`).

---

## 6. O que não foi verificado

- **Contra o backend real:** nenhuma chamada foi feita ao FastAPI; o contrato foi conferido só contra `legenda-ia-endpoints.md` e `04_backend/app/schemas/foto.py`. Com a dependência de produção atual, o caminho real hoje é sempre o 503.
- **No navegador, à mão:** só via Playwright headless (Chromium, viewport Desktop Chrome). Não verificados: layout em celular/PWA, leitor de tela, navegação completa por teclado, contraste do badge e do aviso nos dois temas.
- **Painel dentro do formulário de Ocorrência** (`ocorrencia-form-dialog.tsx`): o teste cobriu só a tela de Visitas; a integração é o mesmo componente, mas o painel dentro do `Dialog` (rolagem `max-h-[90vh]`) não foi visto.
- **Fluxo de upload** depois da mudança: não exercitado (o spec parte de uma foto já vinculada).

---

## 7. Observações para o integrador (propostas, não registradas em `decisoes.md`)

1. **Divergência preexistente de `origem` (fora do escopo, não corrigida):** `foto-upload.tsx` vincula uploads manuais com `origem: "upload"` e `lib/types.ts` declara `OrigemFoto = "lightshot" | "upload" | "camera"`, mas o backend aceita só `"upload_manual" | "lightshot" | "clipboard"` (`04_backend/app/schemas/foto.py`, DEC-39 C). Pela leitura do código, upload por arquivo deve receber 422 ao vincular; não foi testado contra a API. Sugere-se uma tarefa de correção no frontend.
2. **`ApiError` sem `type`:** guardar o `type` do RFC 7807 permitiria distinguir erros pelo sufixo (`legenda-ia-indisponivel`) em vez do status.
3. **DP-10 de BL-34** (editar legenda aprovada sem reaprovar): a edição manual pelo `Input` do card continua um `PUT { legenda }` simples, que mantém `status_validacao_ia = aprovada` e o aprovador anterior. A UI não mudou esse comportamento; depende da decisão do dono.
