# BL-36 — Legenda aprovada no LTIP e no RFIP (RN-16/RN-17, DEC-37 DP-9)

**Status da regra:** DEC-37 DP-9 segue como proposta ainda não aprovada pelo dono (ver `legenda-relatorio.md`).

## Preparação
O worktree estava em `14ead2f`, sem `legenda_foto.py` nem os pipelines do LTIP/RFIP (estavam só em `main`). Fiz `git merge --ff-only main` (local, sem push) para obter T24, LTIP e RFIP.

## O que mudou
- `ltip_pipeline.py`: `_normalizar_ocorrencia` passa cada item de `ocorrencia["fotos"]` por `legenda_para_relatorio` (`foto["legenda"] = ...`). É chamada por `normalizar_contexto`, usado em `renderizar_html`/`gerar_pdf` e `gerar_docx` do LTIP.
- `rfip_pipeline.py`: **sem edição**. Importa `_normalizar_ocorrencia` do LTIP e a chama em seu `normalizar_contexto`, usado em `renderizar_html`/`gerar_pdf` e `gerar_docx`; herda a regra.
- Novo `tests/test_legenda_relatorio_ltip_rfip.py`. Layout, templates, RFO, Cautelar e Residencial intactos.

## Fato relevante
Hoje **nenhum template impresso do LTIP/RFIP imprime legenda de foto** (só "Foto nº" e `descricao` da ocorrência; `grep legenda` nos `.j2` não acha nada). A regra protege o contexto: se um template passar a usar `foto.legenda`, só sai texto aprovado/manual. A `descricao` da ocorrência não é legenda de foto e não foi alterada.
Efeito colateral: `foto["legenda"]` do contexto normalizado passa a ser sempre string (vazia se rascunho sem legenda manual); `legenda_ia_sugerida` nunca é lida.

## Testes (de `04_backend`)
Ambiente local sem `pytest-asyncio`, `asyncpg` e `docxtpl`: instalei-os com pip para o conftest e o DOCX carregarem. PostgreSQL não usado (testes sem banco).

```
python -m pytest tests/test_legenda_relatorio_ltip_rfip.py tests/test_ltip_pipeline.py tests/test_rfip_pipeline.py tests/test_legenda_relatorio.py -q -rs
42 passed, 5 skipped
SKIPPED [2] test_legenda_relatorio_ltip_rfip.py: WeasyPrint/GTK indisponível neste ambiente
SKIPPED [2] test_ltip_pipeline.py: WeasyPrint indisponível (só no container de 05_infra)
SKIPPED [1] test_rfip_pipeline.py: WeasyPrint indisponível (só no container de 05_infra)
```
Os testes de PDF não rodaram aqui; a regra no caminho de PDF é coberta indiretamente pelo teste de `renderizar_html` (mesmo `normalizar_contexto`).

`ruff check .`: após corrigir 1 erro meu, restam 11 pré-existentes (I001, RUF001, RUF005, RUF043 em arquivos que não toquei). `npm` não aplicável (sem mudança no frontend).

## Propostas / pendências
- Se a ficha do LTIP/RFIP ganhar legenda de foto, o template deve usar `ocorrencia.fotos[0].legenda` (já saneada) — decisão de layout, fora desta tarefa.
- Consumir `sinalizar_fotos_ia_em_rascunho` para alertar na geração (pendência herdada de T24).
- Vistoria Cautelar/Residencial: tratadas em `legenda-relatorio-vistorias.md`.
