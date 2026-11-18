# Alerta de fotos com legenda IA em rascunho na emissão (BL-38)

DEC-37 DP-9 segue proposta (só legenda aprovada entra no relatório). Aqui o alerta é só informativo: a emissão continua normalmente (201).

## Formato do campo
`RelatorioEmitidoRead.fotos_ia_em_rascunho: list[uuid.UUID]`, default `[]` (retrocompatível). Vale para `POST /inspecoes/{id}/relatorios/rfo` e `/{tipo}`.

**Escolha: ids de foto, não índices.** O contexto de cada tipo não carrega `status_validacao_ia` e a ordem das fotos difere entre pipelines. Os ids são estáveis e o front os localiza. Ordem da lista: `storage_key`, depois `id`.

## Onde
- `04_backend/app/services/relatorio_service.py:380` `fotos_ia_em_rascunho(db, chaves)`: carrega as `Foto` pelas `storage_key` usadas e chama `sinalizar_fotos_ia_em_rascunho` (`legenda_foto.py:30`).
- `relatorio_service.py:419-420` `emitir_relatorio` usa as chaves de `emissor.extrair_fotos(contexto)` (vale para RFO, LTIP, RFIP e vistorias); `:465` coloca o resultado num atributo transitório (não mapeado) do `Relatorio`.
- `04_backend/app/schemas/relatorio.py:52` campo novo; `04_backend/app/api/v1/relatorios.py:61` `_emitido` o devolve.
- Pipelines e `legenda_foto.py` não foram alterados. A assinatura de `emitir_relatorio` continua devolvendo `Relatorio`.

## Testes
`04_backend/tests/test_relatorio_alerta_ia_rascunho.py`: sem rascunhos (`[]`), com rascunho (devolve o id e emite 201) e legenda aprovada ignorada.

## Comandos e saída (a partir de 04_backend/)
O PostgreSQL local (5433) estava no ar, mas uma migration atrás: rodei `alembic upgrade head` (até `d3e7a1c5f9b2`) antes dos testes.
- `pytest tests/test_relatorio_alerta_ia_rascunho.py tests/test_legenda_relatorio.py tests/test_relatorios_emissao_generica.py tests/test_relatorios_rfo_api.py` → `44 passed, 2 warnings`
- `ruff check .` → `All checks passed!`
- Não rodei a suíte completa nem o frontend (não tocado).

## Pendente
O frontend ainda não exibe o alerta.
