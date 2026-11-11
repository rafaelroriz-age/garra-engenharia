# BL-32 · Portal do Cliente só para o perfil `cliente` (UI)

**Tarefa:** BL-32 · **Papel:** Engenheiro Frontend (`.github/agents/frontend.agent.md`) · **Branch:** `worktree-backlog-T54`
**Contexto:** a T41 (`00_docs/backlog-auto/portal-e2e.md`, spec `03_frontend/e2e/portal.spec.ts`) apontou que `/portal` não controlava o perfil na UI: sem redirecionamento por `role`, qualquer usuário autenticado via o portal. A proteção real é do backend (`/portal/*` responde 403); esta entrega é a camada de UI.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `03_frontend/app/portal/layout.tsx` (novo) | Guarda do portal. Usa `useUsuarioAtual()` (`lib/use-usuario-atual.ts`, `GET /auth/me`, o mesmo hook das telas `edificacoes`, `contratos`, `inspecoes`). Regras abaixo. |
| `03_frontend/e2e/portal-perfil.spec.ts` (novo) | E2E com API mockada (`page.route`), 4 testes. |
| `00_docs/backlog-auto/portal-perfil-ui.md` (novo) | Este registro. |

Não foram alterados: backend, `03_frontend/e2e/portal.spec.ts`, `00_docs/projeto/*`, `BACKLOG.md`.

### Regras da guarda (`app/portal/layout.tsx`)

- Vale para `/portal` e `/portal/*` (o layout cobre também `/portal/documentos`).
- Enquanto `/auth/me` carrega, mostra só um esqueleto com `role="status"`; nenhum conteúdo do portal é renderizado nem busca dados.
- `role === "cliente"`: renderiza o portal normalmente.
- Outro `role` (`auditor`, `auxiliar`): `router.replace("/dashboard")` (home interna, a mesma para onde o login já leva). Nenhuma chamada a `/portal/*` é feita, porque o conteúdo do layout não monta.
- Sem sessão (sem token): o `AppShell` (`components/layout/app-shell.tsx`) já redireciona a `/login`, regra existente, não alterada.
- `/auth/me` sem perfil confirmado (usuário `null`, ex.: token inválido ou falha de rede): `router.replace("/login")`. Decisão deste lote, ver abaixo.

## Testes e comandos

Todos a partir de `03_frontend/`.

| Comando | Resultado |
|---|---|
| `npm ci` | 488 pacotes instalados (`node_modules` não existia no worktree). Aviso não bloqueante: `unrs-resolver@1.12.2` com postinstall não aprovado. |
| `npm run lint` | `✔ No ESLint warnings or errors` (exit 0) |
| `npm run build` | `✓ Compiled successfully`, 10/10 páginas geradas, `/portal` e `/portal/documentos` presentes (exit 0) |
| `npx playwright test e2e/portal-perfil.spec.ts e2e/portal.spec.ts` (contra `next start -p 3100`, `E2E_BASE_URL=http://localhost:3100`) | **11 passed, 1 failed** (ver abaixo) |

Servidor de teste: `next start` na porta **3100** (o que estava em `localhost:3000` respondia 500 e não é deste worktree). Não há backend: todas as chamadas à API são mockadas.

### Detalhe do Playwright

`portal-perfil.spec.ts` (4/4 ok):
- `(1)` auditor em `/portal` → `/dashboard`, sem `#portal-edificacao`, zero chamadas a `/portal/*`.
- `(1b)` auxiliar em `/portal/documentos` → `/dashboard`, zero chamadas a `/portal/*`.
- `(2)` cliente em `/portal` → `?edificacaoId=…`, select com a edificação mockada.
- `(3)` sem sessão em `/portal` → `/login`.

`portal.spec.ts` (7/8 ok):
- `(a)`, `(b)`, `(c)`, `(d1)`, `(d2)`, `(d3)`, `(d4)` ok, sem alteração no código deles.
- **`(e)` falha, esperado.** O teste afirma a lacuna que esta entrega fecha: "perfil auditor … a UI não bloqueia /portal (lacuna)". Ele espera que o auditor permaneça em `/portal` e veja o alerta `Perfil sem acesso ao portal.` vindo do 403. Agora o auditor é redirecionado a `/dashboard`, então o alerta não aparece (`Error: element(s) not found`). A asserção `toHaveURL(/\/portal$/)` passa só porque roda antes do redirecionamento.
  - Não editei `portal.spec.ts` (instrução explícita: só ler). O teste (e) precisa ser reescrito no fechamento de lote para o novo comportamento (espera `/dashboard`, sem alerta de 403); a partir daí ele é a prova da correção.
  - Não reverti a guarda para manter (e) verde, porque isso desfaria o requisito (1).

## Decisões propostas (para o integrador, não aplicadas em `decisoes.md`)

- **DEC-proposta-A:** o portal é guardado na UI por `role` via `GET /auth/me` (`layout.tsx` em `app/portal/`). A UI é só usabilidade; a autorização segue no backend (403).
- **DEC-proposta-B:** perfil não confirmado (`/auth/me` falhou ou usuário `null`) redireciona ao login, e não à home. Motivo: sem perfil confirmado não há como decidir a home; o login recomeça a sessão.

## Pendências e riscos

1. **Branch atrás de `main`:** `worktree-backlog-T54` é ancestral de `main` (`git rev-list --left-right --count main...HEAD` → `258 0`). `portal.spec.ts` (commit `212cc92`, BL-32/T41) existe só em `main` e em `worktree-backlog-T53`, não aqui. Para rodar os testes copiei o arquivo de `main` para `e2e/` e removi a cópia depois; ele **não foi commitado**. O integrador precisa integrar `main` antes de rodar o teste (e) lá.
2. **Teste (e) do `portal.spec.ts`** precisa ser atualizado no lote (ver acima).
3. **401 em `/auth/me`:** `lib/api-client.ts` não trata 401 globalmente (não há redirecionamento por 401). Hoje, token expirado cai em `usuario === null` → login, pelo caminho descrito acima. Outras telas não mudam de comportamento.
4. **Não coberto:** navegação do menu para perfil `cliente` (já era coberto no teste (a) da `portal.spec.ts`) e fluxo de login real (depende de backend).

## Para o fechamento de lote (00_docs/)

- `backlog-tarefas.md`/`backlog-kanban.md`: BL-32 da parte de UI concluída neste worktree; registrar que o teste (e) de `portal.spec.ts` precisa de ajuste.
- `status.md`: resultado acima (11/12 no Playwright dos portais, lint e build verdes).
- `decisoes.md`: propostas A e B.
- `riscos.md`: item 3 (401 não tratado globalmente) e item 1 (branch atrás de `main`).
