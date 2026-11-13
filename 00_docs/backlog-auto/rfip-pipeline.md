# Pipeline de renderização do RFIP (BL-12)

A T13 entregou o extrator e os templates do RFIP (`04_backend/templates/rfip/`, DEC-36). Esta tarefa (T18) acrescenta o pipeline que os renderiza, no mesmo formato do LTIP e das vistorias.

- **Data:** 2026-11-04
- **Branch:** `worktree-backlog-T18` (commit local, sem push). A branch estava atrás da `main`; foi feito `git merge --ff-only main` para trazer T13 e os outros pipelines.
- **Arquivos:** `04_backend/app/services/report_generator/rfip_pipeline.py` (novo), `04_backend/tests/test_rfip_pipeline.py` (novo). Nenhum template, pipeline irmão, documento de gestão ou `01_output-context/` foi alterado.

## API

Módulo `app.services.report_generator.rfip_pipeline`. Os helpers `agrupar_por_sistema`, `_normalizar_ocorrencia`, `_chave_ordem`, `_storage_key_da_foto`, `_mime`, `_logo_data_uri` e `VAZIO` vêm de `ltip_pipeline`; `CAMPOS_RESPONSAVEL` e `_ou_traco` vêm de `vistoria_cautelar_pipeline` (import, sem copiar).

| Função | Assinatura | Resultado |
|---|---|---|
| `normalizar_contexto` | `(contexto) -> dict` | Cópia profunda do contexto completada para o template. Agrupa `ocorrencias` planas em `sistemas` (RN-11), ordena por subsistema e nº da foto, troca campos vazios por '—' (DEC-33), calcula `pontuacao_gut` se faltar. Não muta a entrada. |
| `renderizar_html` | `(contexto, fotos_bytes) -> str` | HTML com Jinja2 (autoescape) e fotos como data URI. |
| `gerar_pdf` | `(contexto, fotos_bytes, destino) -> dict` | WeasyPrint (import preguiçoso). Métricas: `render_html`, `conversao_pdf`, `total`, `n_paginas`, `tamanho_bytes`. |
| `gerar_docx` | `(contexto, fotos_bytes, destino, *, template_path=None) -> dict` | docxtpl com `autoescape=True`. Métricas: `montagem_fotos`, `render_e_salvar`, `total`, `tamanho_bytes`. |

Regras: o módulo não acessa o MinIO (o chamador entrega `fotos_bytes` indexado por `storage_key`); foto referenciada e ausente levanta `KeyError`; foto no DOCX é redimensionada para caber na caixa da ficha (13,78 × 7,29 cm, lida de `layout.json`: `ficha.foto` × `grade.escala_impressao`) sem deformar.

## Campos do contexto

Descobertos no `rfip_template.html.j2` e no `rfip_template.docx` (`DocxTemplate.get_undeclared_template_variables()` = `incluir_resumo`, `responsavel`, `sistemas`) e conferidos com `layout.json`.

| Campo | Onde o template usa | Tratamento no pipeline |
|---|---|---|
| `responsavel.nome`, `.titulo_profissional`, `.crea`, `.email`, `.telefone` | Rodapé (3 linhas) | Vazio → '—'. |
| `logo_data_uri` | Cabeçalho (HTML) | Padrão: `templates/assets/logo-garra.svg`. No DOCX a logo já está embutida no template. |
| `incluir_resumo` | Quadro-resumo após as fichas (DEC-36 C) | Vira booleano; padrão `False`. |
| `sistemas[].nome` | Título `7.N. <nome>`, linha SISTEMA da ficha e do resumo | Vazio → '—'. |
| `ocorrencias` (alternativa a `sistemas`) | — | Cada item precisa de `sistema` (e opcionalmente `sistema_ordem`, `subsistema_ordem`); sem `sistema` levanta `ValueError` (RN-11). |
| `sistemas[].ocorrencias[].seq_numero` | `Foto nº NN` (2 dígitos) | Obrigatório (usado em `%02d`). |
| `.situacao`, `.gut_gravidade`, `.gut_urgencia`, `.gut_tendencia`, `.pontuacao_gut`, `.classificacao`, `.grau_risco`, `.subsistema`, `.localizacao`, `.descricao` | Células da ficha e do resumo | Vazio → '—'. Notas `3.0` → `3`. `pontuacao_gut` = G×U×T quando as três existem. |
| `.tipo_anomalia` / `.tipo_falha` | Célula "TIPO DE <classificação>" | Se os dois faltam, `tipo_falha` = '—'. |
| `.fotos[0].storage_key` | Foto da ficha | Entrada do chamador; vira `foto_data_uri` (HTML) e `foto_docx` (`InlineImage`, DOCX). Sem foto, a célula fica vazia. |
| `numero_pagina` (placeholder em `layout.json`) | Nenhum template o usa | Não faz parte do contexto: HTML usa `counter(page)` e DOCX usa o campo `PAGE`, ambos a partir de 1 (DEC-36 B). |

Ficam fora do contexto, por serem rótulos fixos do template: "SITUAÇÃO", "GRAVIDADE", cabeçalhos do resumo etc. Também não foram inventados campos de capa, contrato ou edificação: o RFIP derivado da planilha não os tem.

## Testes

`04_backend/tests/test_rfip_pipeline.py`: 12 testes com contexto sintético (nome, CREA, e-mail e telefone fictícios), sem tocar em `01_output-context/`.

- contexto: agrupamento e ordem (RN-11), não mutação, vazio → '—', `incluir_resumo` booleano, `sistemas` já agrupados, ocorrência sem sistema;
- HTML: títulos `7.N.`, 4 fichas, 3 data URIs (uma ocorrência sem foto), rodapé, autoescape de `&`/`<`/`>`, sem `{{`/`{%` sobrando, quadro-resumo opcional, '—' nos vazios, `KeyError`;
- DOCX: fichas, rodapé com `PAGE`, 3 fotos + logo em `word/media/`, texto com `&`/`<` literal, foto 5:1 limitada pela largura da caixa sem deformar, `KeyError`, `template_path`;
- PDF: `skip` com motivo se o WeasyPrint não carregar.

### Comandos e saídas (a partir de `04_backend/`, venv do checkout principal)

```text
$ python -m pytest -q -p no:cacheprovider tests/test_rfip_pipeline.py tests/test_rfip_templates.py
27 passed, 1 skipped, 1 warning in 16.80s
# skip: "WeasyPrint indisponível nesta máquina (OSError): só carrega no container de 05_infra"

$ ruff check app/services/report_generator/rfip_pipeline.py tests/test_rfip_pipeline.py
All checks passed!

$ ruff check .
Found 16 errors.      # nenhum nos arquivos desta tarefa; estão em ocorrencia_repository.py,
                      # vistoria_cautelar_layout_extractor.py e testes de outras tarefas

$ python -m pytest -q -p no:cacheprovider        # suíte completa
8 failed, 137 passed, 6 skipped, 6 warnings, 181 errors in 194.01s
```

**A suíte completa não passou, por causa do ambiente, não desta tarefa.** O PostgreSQL de `05_infra` respondeu em `localhost:5433` (`Test-NetConnection` = True), mas os testes que sobem o app falham com `ValueError: the greenlet library is required to use this function. No module named 'greenlet._greenlet'`: o venv do checkout principal está sem o `greenlet` funcional, o que quebra o SQLAlchemy assíncrono. Os 8 `FAILED` e os 181 `ERROR` estão em `test_auth`, `test_edificacoes`, `test_fotos*`, `test_responsaveis`, `test_seguranca`, `test_visitas*` etc., todos fora do RFIP. Para validar a suíte inteira é preciso reinstalar o `greenlet` no venv (ou rodar no container). Os testes que não usam banco (todos os de pipeline e templates) passam.

## Pendências

- **PDF real (HT-09):** o WeasyPrint não carrega neste Windows, então nenhum PDF do RFIP foi renderizado. No container, rodar `test_pdf_gerado_com_weasyprint` e conferir lado a lado com o original (logo no `@top-right`, 2 fichas por página sem quebra forçada, fontes Calibri/Cambria ou Carlito/Caladea, página de resumo com margens próprias).
- **Mapeamento banco → contexto:** nenhum código monta ainda o contexto a partir de `Inspecao`/`Ocorrencia`/`Foto`/`Contrato`. Falta definir de onde vêm `responsavel.*` (usuário/ART da inspeção) e se `incluir_resumo` é escolha do usuário. Também falta o chamador que busca os bytes no MinIO por `storage_key` e expõe o endpoint de geração.
- **Foto única por ocorrência:** como no LTIP, só `fotos[0]` entra na ficha; a ficha do RFIP tem uma área de foto.
- **Quadro-resumo no DOCX:** a coluna "Imagem" do resumo não recebe imagem no HTML nem no DOCX (o template só imprime "Foto nº NN"). Se o cliente espera a miniatura, é mudança no gerador de templates (T13), não aqui.
- **Importação de helpers privados** (`_normalizar_ocorrencia`, `_ou_traco` etc.): funciona, mas acopla o RFIP a nomes com `_`. Sugestão para a limpeza de lote: promover os helpers comuns dos pipelines a um módulo compartilhado (não feito agora porque os arquivos dos outros pipelines não podem ser editados).

## Decisões propostas

Nenhuma decisão nova. A tarefa aplica DEC-33 (traço), DEC-35 (sem acesso ao MinIO, mesmas métricas) e DEC-36 (numeração em 1; resumo opcional).
