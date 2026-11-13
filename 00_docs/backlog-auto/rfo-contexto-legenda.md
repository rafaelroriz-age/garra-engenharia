# Contexto do RFO usa `legenda_para_relatorio` (DEC-47, item 1)

Tarefa: remover `legenda_aprovada` de `report_generator/rfo_contexto.py` e fazer `montar_contexto_rfo` usar o helper comum, como `rfo_pipeline`, `ltip_pipeline` e as vistorias (DEC-37 DP-9, T24/T36/T37).

## O que mudou

- `04_backend/app/services/report_generator/rfo_contexto.py`
  - Removidos `legenda_aprovada(foto)` e a constante `LEGENDA_APROVADA`.
  - Importado `legenda_para_relatorio` de `legenda_foto.py`.
  - `_foto_ctx` passa a usar `legenda_para_relatorio(foto) or None`. Só `legenda` entra no contexto; `legenda_ia_sugerida` nunca entra, qualquer que seja `status_validacao_ia`.
- `04_backend/tests/test_rfo_contexto.py`
  - Removido `test_legenda_pendente_nao_entra` (usava objeto simulado com `legenda_status`, campo que não existe em `Foto`).
  - Novo fixture `usuario_auditor` (Usuario real, apagado no teardown; necessário porque `status_validacao_ia='aprovada'` exige `aprovado_por_id`/`aprovado_em`).
  - Novo fixture `rfo_legendas`: uma visita com 4 `Foto` persistidas:
    1. legenda manual, sem IA;
    2. IA em `rascunho`, sem legenda manual;
    3. IA `aprovada`, sem legenda manual;
    4. legenda manual + IA em `rascunho`.
  - `test_legenda_no_contexto_usa_legenda_para_relatorio`: confere que sai `"Manual humana"`, `None`, `None` e `"Manual prevalece"`.
  - `test_legenda_ia_nao_aparece_no_html_renderizado`: renderiza o template e confere que nenhuma sugestão de IA aparece no HTML.

Nenhuma migration nem coluna nova. Não foram editados documentos de gestão (`00_docs/projeto/*`, `BACKLOG.md`).

## Comandos e resultados

Ambiente: venv Python 3.12 em `$CLAUDE_JOB_DIR/tmp/venv` com `requirements.txt` + `pytest pytest-asyncio ruff`. Python 3.14 não tem wheel de `pillow<11`.

```
python -m pytest tests/test_rfo_contexto.py tests/test_legenda_relatorio.py -q
```
Resultado: **não rodou**. Falha na coleta de `test_rfo_contexto.py` (antes de qualquer teste):
```
OSError: cannot load library 'libgobject-2.0-0' ... WeasyPrint could not import some external libraries
```
Causa: WeasyPrint precisa de Pango/GObject nativos, ausentes neste Windows. O Docker também não está instalado aqui, então não houve fallback para o container.

Verificação possível sem o banco:
```
python -m pytest tests/test_legenda_relatorio.py -q
→ 8 passed in 0.43s
ruff check .
→ All checks passed!
python -m py_compile app/services/report_generator/rfo_contexto.py tests/test_rfo_contexto.py
→ OK
```

**Pendente (não verificado):** os testes com banco de `test_rfo_contexto.py` (incluindo os 2 novos) não rodaram. O PostgreSQL de `05_infra/docker-compose.yml` (localhost:5433) não estava no ar. Para fechar, rodar a partir de `04_backend/` com o banco no ar e com WeasyPrint disponível (ou no container):
```
python -m pytest tests/test_rfo_contexto.py tests/test_legenda_relatorio.py
ruff check .
```

## Observações para o fechamento de lote (não editado aqui)

- `00_docs/backlog-auto/rfo-contexto-banco.md`: a seção "Correção do fechamento de lote" já diz que a lacuna 1 e a proposta P1 estão obsoletas. Esta tarefa resolve a lacuna 1 (usa `legenda_para_relatorio`). A P1 (`Foto.legenda_status`) fica descartada, como indicado no próprio doc.
- Pendências desse doc que continuam abertas: lacunas 2 a 6 e propostas P2/P3 (ocorrências no RFO, validação de completude, `Foto.data_uri`, assinaturas/ART).
- Nenhuma decisão nova proposta.
