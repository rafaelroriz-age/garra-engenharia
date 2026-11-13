# T37 — Legenda aprovada nas Vistorias Cautelar e Residencial (BL-36)

Regra: só a `legenda` entra no relatório; `legenda_ia_sugerida` nunca é impressa, em qualquer status (RN-16/RN-17, DEC-37 DP-9, ainda proposta pendente de confirmação do dono; ver `legenda-relatorio.md`). A aprovação copia o texto para `legenda`.

## O que mudou
- `vistoria_cautelar_pipeline.py`: `normalizar_contexto` passa cada `figura` por `legenda_para_relatorio` (depois `_ou_traco`).
- `vistoria_residencial_pipeline.py`: `normalizar_contexto` passa cada `foto` por `legenda_para_relatorio` (depois `_preencher`).
- Como PDF (`_renderizar`/`renderizar_html`) e DOCX (`gerar_docx`) já consomem `normalizar_contexto`, um único ponto cobre os dois formatos. O contexto recebido não é mutado.
- Preservado o comportamento da T28 (`foto_fetcher`, `garra-foto:<n>`, data URI em `renderizar_html`). Templates, `layout.json`, `rfo`, `ltip` e `rfip` intocados.
- Novo `04_backend/tests/test_legenda_relatorio_vistorias.py`: por pipeline, IA em rascunho não aparece, IA aprovada (texto em `legenda`) aparece sem a sugestão crua, manual aparece; verificado em contexto normalizado, HTML, DOCX e PDF. Sem banco.
- Preparo: a branch do worktree estava atrás da `main` (sem T24/T28); fiz `git merge --ff-only main` localmente.

## Resultados
- `pytest tests/test_legenda_relatorio_vistorias.py tests/test_vistoria_cautelar_pipeline.py tests/test_vistoria_residencial_pipeline.py tests/test_pipelines_url_fetcher.py` (venv de `04_backend/.venv`): **42 passed, 6 skipped**.
- Pulados (sem WeasyPrint/GTK no Windows, `OSError`): 2 testes de PDF novos (`skipif` explícito), 1 PDF da cautelar, 1 PDF da residencial, 2 do `URLFetcher` em `test_pipelines_url_fetcher.py`. O caminho PDF real **não foi executado**; falta rodar no container de `05_infra/`. O DOCX e o HTML (fonte do PDF) foram verificados.
- Também: `tests/test_legenda_relatorio.py` 8 passed.
- `ruff check .`: **11 erros, todos pré-existentes** e fora do escopo (`app/scripts/vistoria_cautelar_layout_extractor.py` RUF001; `test_foto_origem_enum`, `test_ocorrencias_regras`, `test_storage_legenda_ia`, `test_vistoria_cautelar_templates` I001/RUF005; `test_vistoria_cautelar_pipeline` RUF043). Nos arquivos tocados: passou.
- Suíte completa e testes com PostgreSQL (localhost:5433): não executados. Frontend não tocado.

## Decisão proposta
Nenhuma nova. Segue pendente a confirmação de DEC-37 DP-9 pelo dono; `sinalizar_fotos_ia_em_rascunho` continua sem consumidor nos pipelines (alerta ao gerar fica para tarefa própria).
