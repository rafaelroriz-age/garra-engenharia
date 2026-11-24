# T109 — Portal: campo `vigente` na listagem de relatórios (DEC-48 P1)

## O que mudou
- `PortalRelatorioRead` (`04_backend/app/schemas/portal.py`): novo campo `vigente: bool`.
- `portal_service.listar_relatorios`: `vigente` calculado em Python sobre a lista já filtrada por contratante (sem nova query): maior versão do mesmo `(inspecao_id, tipo)` entre os relatórios visíveis ao cliente. Comparação numérica (`V10 > V9`). Ordenação, filtro e download inalterados; nada de outro contratante entra no cálculo.
- Testes: removido o `xfail(strict)` de `test_listagem_sinaliza_qual_versao_e_a_vigente` (asserção intacta); novos `test_cada_tipo_tem_sua_propria_versao_vigente` e `test_relatorio_com_uma_so_versao_e_vigente`.

## Resultado
- `pytest tests/test_portal_versoes_relatorio.py` (PostgreSQL localhost:5433): **18 passed**.
- `ruff check .`: All checks passed.
- `pytest -k portal` global não completou: coleta de `tests/test_rfo_contexto.py` falha por falta da libpango/WeasyPrint no Windows (pré-existente); `test_portal_cliente.py`/`test_rbac_portal.py` não concluíram a tempo (os de download dependem do storage real, já apontado em portal-versoes-relatorio.md). Não rodei `npm` (frontend intocado).

## Proposta para o frontend (NÃO implementada)
`03_frontend/lib/types.ts` (`PortalRelatorio`) ganha `vigente: boolean`; em `03_frontend/app/portal/documentos/page.tsx` exibir selo "vigente" nos itens com `vigente === true` e tratar os demais como "versões anteriores". `e2e/portal.spec.ts` também consome a rota.
