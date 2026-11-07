# Aprovação de legenda IA restrita ao auditor — frontend (DEC-42 A e B)

- **Tarefa:** T34 (lado frontend), depende da regra de backend da T33 (`legenda-ia-aprovacao-auditor.md`, commit `225974d`).
- **Branch:** `worktree-backlog-T34` (sem push). Commit: `feat(frontend): aprovação de legenda IA restrita ao auditor (DEC-42)`, `Refs DEC-42`.
- **Tocado:** `03_frontend/components/legenda-ia-painel.tsx`, `03_frontend/e2e/legenda-ia-aprovacao.spec.ts` (novo), `03_frontend/e2e/legenda-ia.spec.ts` (um teste ajustado), este doc. Sem `api-client.ts`, `types.ts`, `use-usuario-atual.ts` nem outros componentes.
- **Variáveis de ambiente novas:** nenhuma. **Dependências novas:** nenhuma.
- **Documentos de gestão não editados:** `backlog-tarefas.md`, `backlog-kanban.md`, `status.md`, `decisoes.md`, `riscos.md`, `BACKLOG.md`.

---

## 1. Pré-requisito de ordem

O worktree estava em `14ead2f`, 170 commits atrás de `main`: não tinha a T26 (`legenda-ia-painel.tsx`) nem a regra de backend DEC-42 (`225974d`). Ação: `git merge --ff-only main` (fast-forward, sem commit de merge) para `d693ca5`. Só então a tarefa pôde ser feita.

---

## 2. Comportamento

### A. Só o auditor aprova (DEC-42 A)

- O painel lê o papel com `useUsuarioAtual()`. Se `isAuditor` for falso, o botão «Aprovar legenda» (e o bloco de confirmação) **não aparece**.
- No lugar aparece o texto: «A aprovação é feita pelo auditor responsável.» Enquanto o perfil carrega, nada é mostrado (evita piscar o texto).
- `auxiliar` continua vendo e usando «Gerar», «Gerar nova sugestão com IA» e o campo de texto editável.
- A checagem de papel é só usabilidade: o backend já responde 403 ao `auxiliar` que tenta aprovar (T33).

### B. Editar ou regerar legenda aprovada desfaz a aprovação (DEC-42 B)

- Quando `status_validacao_ia === "aprovada"`, aparece um aviso: «Esta legenda já está aprovada» / «Editar o texto ou gerar nova sugestão desfaz a aprovação: a legenda volta a rascunho e só entra no relatório depois de aprovada de novo.»
- Se o texto do campo for diferente da legenda aprovada, aparece o botão «Salvar edição (desfaz a aprovação)». Ele faz `PUT /fotos/{id}` com `{ legenda }` (sem `aprovar_legenda_ia`). O backend zera `aprovado_*` e devolve `status_validacao_ia = "rascunho"`.
- O selo («Rascunho — aguardando aprovação» / «Aprovada em …») vem sempre das props `foto` que o pai atualiza com a resposta do backend. O componente não presume o status localmente.
- Mensagens de sucesso seguem a resposta: se o backend devolveu `rascunho`, o texto diz que a aprovação foi desfeita. Regerar com foto já aprovada e resposta `rascunho` mostra «A aprovação anterior foi desfeita».
- Como a edição sem aprovar não é mais um caminho que deixa a legenda aprovada, o botão «Aprovar legenda» de quem é auditor reaprova o texto revisado (com confirmação, como antes).

### Chamada nova

`api.put<Foto>("/fotos/{id}", { legenda } satisfies FotoUpdateInput)`, chamada direto no componente com `api` já exportado por `api-client.ts`. Não foi criado método novo em `legendaIA`, por causa do `toca` da tarefa.

---

## 3. Testes

### `e2e/legenda-ia-aprovacao.spec.ts` (novo, 4 testes, API mockada)

| Teste | Verifica |
|---|---|
| auxiliar não vê «Aprovar» e recebe a orientação | `Aprovar legenda` ausente; texto explicativo visível; campo editável e «Gerar nova sugestão» habilitados |
| auditor vê «Aprovar» e aprova após confirmação | botão visível; nada é enviado antes da confirmação; `PUT` com `{ legenda, aprovar_legenda_ia: true }`; selo «Aprovada em» |
| editar legenda aprovada mostra aviso e volta a rascunho | aviso visível; botão «Salvar edição» envia `{ legenda }` sem aprovar; selo «Aprovada» some e aparece «Rascunho»; mensagem «A aprovação foi desfeita» |
| gerar nova sugestão em aprovada volta a rascunho | aviso visível antes; resposta `rascunho` do `POST …/gerar` atualiza selo e mostra «A aprovação anterior foi desfeita» |

### `e2e/legenda-ia.spec.ts` (T26, ajuste de 1 linha)

O teste «gera rascunho, exige texto e confirmação, e aprova o texto revisado» usava `auxiliar` para aprovar, o que o DEC-42 A proíbe. Foi trocado para `auditor`, com comentário. Os outros dois testes do arquivo não mudaram.

---

## 4. Comandos e saídas

Todos a partir de `03_frontend`. `node_modules` não existia no worktree; rodou `npm ci --no-audit --no-fund` (aviso de `install-scripts` para `unrs-resolver`, sem erro). `npm audit fix` não foi rodado.

| Comando | Saída |
|---|---|
| `npm run lint` | `✔ No ESLint warnings or errors` (exit 0) |
| `npm run build` | build concluído; tabela de rotas exibida (`/inspecoes/[id]/visitas` 3.9 kB / 129 kB, `/inspecoes/[id]/ocorrencias` 4.64 kB / 129 kB). O exit code não foi capturado, por causa do `tail` no comando |
| `npx next start -p 3123` (build acima) + `E2E_BASE_URL=http://localhost:3123 npx playwright test e2e/legenda-ia-aprovacao.spec.ts e2e/legenda-ia.spec.ts` | `7 passed (13.5s)` |

Os specs `rfo.spec.ts` e `ltip.spec.ts` (stack real) **não rodaram**: exigem backend, banco e MinIO via `docker compose` em `05_infra`, e o docker não está disponível neste shell. Não há resultado inventado para eles.

---

## 5. O que não foi verificado

- **Contra o backend real:** nada foi chamado no FastAPI. O contrato de 403 (auxiliar aprovar) e de `rascunho` após `PUT` sem aprovar vem da T33, que também não foi executada aqui (pytest não rodou nesta tarefa).
- **Caminho pelo campo «Legenda da foto» do card** (`foto-upload.tsx`, `PUT { legenda }` direto): o backend agora invalida a aprovação ao mudar a legenda de foto aprovada, mas **não verifiquei** se o card repassa a `FotoRead` devolvida ao pai, nem se o selo do painel fica coerente. Pelo código lido, o card só faz `onChange`; vale conferir no fechamento de lote.
- **Layout em celular, leitor de tela, teclado e temas claro/escuro:** não verificados.

---

## 6. Propostas para o integrador (não registradas em `decisoes.md`)

1. **Campo da legenda no card (`foto-upload.tsx`):** avaliar se a edição direta ali também deve mostrar o aviso de DEC-42 B, ou se deve ser removida para fotos aprovadas, para não haver duas portas de edição com comportamentos diferentes.
2. **`ApiError` sem `type`** (já listado na T26): permitiria distinguir `403` de permissão de outros erros sem depender só do status.
3. **Tipagem de `PUT /fotos/{id}`:** o `api.put` é usado direto no painel com `FotoUpdateInput`. Se o time preferir, o método pode virar `legendaIA.salvarEdicao` em `api-client.ts` numa tarefa com `toca` para esse arquivo.
