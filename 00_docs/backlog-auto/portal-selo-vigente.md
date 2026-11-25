# T116 — Portal do Cliente: selo "vigente" na lista de documentos

Origem: T109 (campo `vigente` em `GET /portal/relatorios`, ver `T109-portal-versao-vigente.md`).

## O que mudou
- `03_frontend/lib/types.ts` (`PortalRelatorio`): novo campo `vigente: boolean`, espelhando o schema `PortalRelatorioRead` do backend.
- `03_frontend/app/portal/documentos/page.tsx`: na coluna "Versão", após o número da versão, exibe o `Badge` existente (`components/ui/badge.tsx`, variante `default`) com o texto "Vigente" quando `relatorio.vigente === true`. A célula passou a usar `className="space-x-2"` com um `<span>` para a versão, como os botões de download já fazem.
- Não há mudança em filtros, ordenação, download ou regras de negócio. Itens com `vigente: false` continuam sem selo, sem texto adicional.

## Fora de escopo (não feito)
- `e2e/portal.spec.ts` consome a rota, mas não foi alterado nem executado (não faz parte do `Pronto`).
- Nenhum teste unitário novo: o `test:unit` atual cobre só `lib/sw-cache` e `lib/modo-leitura`, e a lógica nova é uma renderização condicional sem função pura extraível.

## Resultado dos comandos (em `03_frontend`)
- `npm ci`: 489 pacotes instalados (node_modules não estava no worktree). Avisos de `install-scripts` (`unrs-resolver`) não afetaram o resultado.
- `npm run lint` → `✔ No ESLint warnings or errors` (exit 0).
- `npm run test:unit` → 23 testes, 23 pass, 0 fail.
- `npm run build` → build concluído, rota `/portal/documentos` gerada (exit 0).
- `NEXT_PUBLIC_BASE_PATH` não foi definido, então `MSYS_NO_PATHCONV` não foi necessário.

## Proposta para o integrador (NÃO aplicada)
- Nenhuma decisão nova. Ao fechar o lote, apenas atualizar `backlog-tarefas.md`/`backlog-kanban.md` (status de T116) e, se houver, o `e2e/portal.spec.ts` numa tarefa futura para validar o selo no E2E.
