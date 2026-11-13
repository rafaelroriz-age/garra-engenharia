# E2E offline online-first (DEC-26) — T78

**Status: NÃO EXECUTADA — pré-requisito ausente neste worktree.**

## Verificação do pré-requisito

- `03_frontend/public/` contém apenas `brand/`, `icon.svg` e `manifest.json`; **não existem** `sw.js` nem `offline.html`.
- `git ls-files` na branch `worktree-backlog-T78` não retorna nenhum arquivo de Service Worker.
- O commit `d374837` ("feat(frontend): service worker de leitura e fallback offline (DEC-26)", tarefa A/T77) existe, mas está contido apenas em `main`; a branch deste worktree foi criada antes dele e não o inclui.
- Conforme a instrução da tarefa, parei antes de escrever o spec. Não rodei nada (nem Playwright, nem lint, nem PostgreSQL/stack).

## O que já foi levantado para a retomada

- E2E existentes: `03_frontend/e2e/*.spec.ts`, helpers em `e2e/helpers.ts` e `e2e/inspecao-helpers.ts`, config em `03_frontend/playwright.config.ts`, scripts `test:e2e`, `test:e2e:ui`, `test:e2e:report` no `package.json`. Reutilizar os helpers de login/seed.
- `e2e/visitas-ocorrencias.spec.ts` é o ponto de partida para as ações de escrita (criar visita/ocorrência).
- O spec `offline-dec26` precisará de config Playwright separada (ex.: `playwright.offline.config.ts`) com `webServer` em `npm run build && npm run start`, pois o SW só registra em produção. Não alterar o `playwright.config.ts` atual.

## Como retomar

1. Integrar `main` (ao menos `d374837`) nesta branch (`git merge main` no worktree) ou refazer a tarefa a partir de `main`.
2. Subir PostgreSQL/stack (`docker compose` em `05_infra/`, localhost:5433) e o backend.
3. Executar os passos 2–5 da tarefa (spec, `npx playwright test`, `npm run lint`, atualizar este Doc).

## Lacunas / propostas

Nenhuma avaliada ainda: a UI de erro de escrita sem rede não foi inspecionada.
