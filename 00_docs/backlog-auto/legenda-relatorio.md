# BL-38 — Legenda de foto no relatório (backend)

**Status da regra:** DEC-37 DP-9 é **proposta ainda não aprovada pelo dono**. A implementação segue a proposta e pode mudar.

## Regra implementada
Legenda impressa = sempre `legenda` (trim). `legenda_ia_sugerida` nunca entra no relatório.

| `status_validacao_ia` | Impresso |
|---|---|
| NULL (manual/legada) | `legenda` |
| `aprovada` | `legenda` |
| `rascunho` | `legenda` (manual/anterior; vazio se não houver) |

## O que mudou
- Novo `04_backend/app/services/report_generator/legenda_foto.py` (funções puras, aceitam objeto ou dict): `legenda_para_relatorio`, `foto_ia_em_rascunho`, `sinalizar_fotos_ia_em_rascunho` (índices das fotos IA ainda em rascunho).
- `rfo_pipeline.py`: `gerar_docx` usa `legenda_para_relatorio`; `gerar_pdf` normaliza `foto["legenda"]` na cópia do contexto antes do render (o template já imprime `foto.legenda`). Template, layout.json e demais campos intactos.
- Novo `04_backend/tests/test_legenda_relatorio.py` (8 testes, sem banco).

## Por pipeline
- **rfo_pipeline.py:** aplicado (PDF e DOCX).
- **ltip / rfip / vistoria_cautelar / vistoria_residencial:** **não existem** neste worktree (só `rfo_pipeline.py` em `report_generator/`). Nada aplicado; quando criados, devem usar `legenda_para_relatorio`.
- O model `foto.py` deste worktree ainda não tem `legenda_ia_sugerida`/`status_validacao_ia` (T22 não integrada aqui); não alterei models. O helper usa `getattr`/`dict.get`, então funciona antes e depois da T22.

## Testes
- `pytest tests/test_legenda_relatorio.py`: **8 passed**. O módulo é carregado por caminho porque o `__init__` do pacote importa WeasyPrint (não carrega no Windows: `libgobject-2.0-0`).
- `pytest tests/test_brand_assets.py`: 20 passed.
- `tests/test_rfo_templates.py` e `tests/test_ltip_templates.py`: **não rodaram** (erro de coleta: `pdfplumber` ausente no ambiente local; testes com WeasyPrint também não rodam no Windows).
- Testes que exigem PostgreSQL (localhost:5433): não executados.
- `ruff check` nos arquivos tocados: passou. `ruff check .` completo: 214 erros pré-existentes (fora do escopo, não corrigidos).

## Pendências
- Integração com upload/edição da legenda e anotação visual de "rascunho" no frontend: BL-35/BL-39.
- Usar `sinalizar_fotos_ia_em_rascunho` para alertar na geração (ainda não consumido).
- Aplicar o helper nos demais pipelines quando existirem.
- Confirmar DEC-37 DP-9 com o dono.
