# BL-17 — Pipeline de renderização do LTIP

Tarefa D (pendência "pipeline de renderização" de BL-17). Data: 2026-11-04. Branch: `worktree-backlog-T05`.

BL-17 já gerava os templates em `04_backend/templates/ltip/` (`layout.json`, `ltip_template.html.j2`, `ltip_template.docx`) via `app/scripts/build_ltip_templates.py`. Esta tarefa cria o pipeline que preenche esses templates com dados e gera o PDF e o DOCX, espelhando `app/services/report_generator/rfo_pipeline.py` (ADR-13/DEC-25, ADR-01, ADR-04, RF-06, RN-11).

## Arquivos

| Caminho | Mudança |
|---|---|
| `04_backend/app/services/report_generator/ltip_pipeline.py` | novo: pipeline do LTIP |
| `04_backend/tests/test_ltip_pipeline.py` | novo: 12 testes (contexto, HTML, DOCX, PDF) |
| `04_backend/app/services/report_generator/__init__.py` | atalhos do RFO passam a ser resolvidos sob demanda (PEP 562), ver "Desvio de escopo" |

Templates, `rfo_pipeline.py`, `build_ltip_templates.py` e `01_output-context/` não foram alterados.

## API criada (`app.services.report_generator.ltip_pipeline`)

Mesma forma do `rfo_pipeline`: `contexto` (dict) + `fotos_bytes` (`dict[storage_key, bytes]`) + `destino` (`Path`), devolvendo métricas.

| Função | Entrada → saída |
|---|---|
| `normalizar_contexto(contexto) -> dict` | completa o contexto com o que o template usa; faz cópia profunda e não altera a entrada |
| `agrupar_por_sistema(ocorrencias) -> list[dict]` | ocorrências planas → `[{"nome", "ordem", "ocorrencias"}]` (RN-11) |
| `renderizar_html(contexto, fotos_bytes) -> str` | Jinja2 com autoescape; a foto de cada ficha entra como data URI (JPEG ou PNG) |
| `gerar_pdf(contexto, fotos_bytes, destino) -> dict` | HTML → WeasyPrint. Métricas: `render_html`, `conversao_pdf`, `total`, `n_paginas`, `tamanho_bytes` (as mesmas do RFO) |
| `gerar_docx(contexto, fotos_bytes, destino, *, template_path=None) -> dict` | docxtpl com `autoescape=True`. Métricas: `montagem_fotos`, `render_e_salvar`, `total`, `tamanho_bytes` |

Storage e fotos, como no RFO: o módulo não acessa o MinIO. Quem chama baixa os bytes e os entrega indexados por `storage_key`, e redimensiona as fotos antes se precisar (`rfo_pipeline.otimizar_imagem`). Cada ocorrência mostra a primeira foto de `fotos` (`[{"storage_key": ...}]`, como na relação `Ocorrencia.fotos`). Ocorrência sem foto gera ficha sem imagem. Se uma foto referenciada não estiver em `fotos_bytes`, o pipeline levanta `KeyError` com o `storage_key` e o nº da foto.

O WeasyPrint é importado dentro de `gerar_pdf`, de forma preguiçosa. Contexto, HTML e DOCX funcionam sem ele.

## Campos do contexto

Os nomes saem dos placeholders de `ltip_template.html.j2` e dos que `build_ltip_templates.gerar_docx` grava no `.docx`. Não foi inventado nenhum campo de template.

| Bloco | Campos que o template lê | O que o pipeline faz |
|---|---|---|
| Capa | `logo_data_uri`, `fiscal.nome`, `fiscal.crea`, `data_emissao` | logo SVG de `templates/assets/logo-garra.svg` como padrão; `data_emissao` em `date`/`datetime` sai como `dd/mm/aaaa` (padrão: data de hoje); texto é mantido como veio |
| Edificação | `edificacao.nome` (só no `<title>` do HTML) | `{}` como padrão |
| Capítulos 1–6 e 8 | `introducao_paragrafos`, `consideracoes_preliminares_paragrafos`, `objetivo_paragrafos`, `objeto_paragrafos`, `metodologia_paragrafos`, `documentacao_analisada_paragrafos`, `conclusao_paragrafos` | aceita a lista pronta ou o texto livre em `<chave>` (um parágrafo por linha não vazia); padrão `[]` |
| Relatório fotográfico (RN-11) | `sistemas[].nome`, `sistemas[].ocorrencias[]` | aceita `sistemas` já agrupado ou `ocorrencias` planas com `sistema` (nome) e, opcionalmente, `sistema_ordem`/`subsistema_ordem` (colunas `ordem` do gabarito). Ordem: sistema pela `ordem` (sem ela, pela primeira aparição); dentro do sistema, por `subsistema_ordem`, nome do subsistema e `seq_numero`. Ocorrência sem sistema → `ValueError` |
| Ficha da ocorrência | `seq_numero`, `foto_data_uri` (HTML), `situacao`, `prioridade`, `gut_gravidade`, `gut_urgencia`, `gut_tendencia`, `pontuacao_gut`, `classificacao`, `tipo_anomalia`/`tipo_falha`, `grau_risco`, `subsistema`, `localizacao`, `descricao` | nomes iguais aos do modelo `Ocorrencia`. Nota GUT em `Float` inteiro sai sem `.0`. `pontuacao_gut` = G×U×T quando as três notas existem. Vazio/`None` vira `—`, porque o DOCX não tem fallback e imprimiria `None`. `prioridade = 0` (não aplicável, RN-04/lacuna #10) é preservado |
| Emitente | `fiscal.nome`, `fiscal.crea`, `contrato.art_fiscalizacao` | `{}` como padrão |

O rodapé do emitente (CREA e contato) e a numeração de página estão fixos no template: `@page` do HTML e rodapé da seção do DOCX, gravados a partir do `layout.json`. Nenhum campo do contexto os alimenta.

A regra de 2 fichas por página também está no template (`.ficha { width: 48% }` + `page-break-inside: avoid`). O pipeline só entrega as ocorrências na ordem RN-11.

## O que ficou fora

1. **Conferência visual do PDF (HT-09).** Este ambiente não gera PDF. Ainda falta comparar o PDF com o original (capa, 2 fichas por página, quebras por sistema e rodapé). O teste de PDF só confere que o arquivo é um PDF válido e tem ≥ 11 páginas.
2. **Foto no DOCX.** O `ltip_template.docx` versionado não tem placeholder de imagem na ficha (`build_ltip_templates.gerar_docx` escreve "Foto nº NN" e a tabela, mas nenhum `{{ ocorrencia.foto }}`). O pipeline já entrega `ocorrencia.foto` como `InlineImage` (80 mm). O teste `test_docx_embute_foto_quando_o_template_tem_o_placeholder` prova que a foto entra assim que o template tiver o placeholder. **Sugestão (BL-17):** incluir o parágrafo `{{ ocorrencia.foto }}` logo após o rótulo "Foto nº" em `build_ltip_templates.gerar_docx` e regerar o template.
3. **Fila Celery, endpoint e persistência no MinIO** (ADR-06, §5 da arquitetura). O RFO também não tem; o módulo expõe só as funções síncronas.
4. **Consulta ao banco** (montar o contexto a partir de `Inspecao`/`Ocorrencia`/`Foto`). O pipeline recebe dicts; quem monta é o futuro serviço ou worker.
5. **Sumário** do laudo original: o template derivado não tem.

## Desvio de escopo

`app/services/report_generator/__init__.py` fazia `from .rfo_pipeline import gerar_docx, gerar_pdf, otimizar_imagem` no import do pacote. Como `rfo_pipeline` importa `weasyprint` no topo, **qualquer** `import app.services.report_generator.ltip_pipeline` falhava fora do container, e os testes de DOCX não rodariam no Windows. Troquei por um `__getattr__` (PEP 562), que resolve os mesmos três nomes sob demanda. A API pública do pacote não mudou. O único outro consumidor, `app/scripts/benchmark_relatorio_geracao.py`, importa o submódulo `rfo_pipeline` direto e não é afetado.

## Sugestões de refatoração (não feitas, fora de `toca`)

- **Módulo comum `report_generator/comum.py`** com `_em_itens`/`_em_paragrafos`, `_logo_data_uri` e `otimizar_imagem`. Hoje os dois primeiros estão duplicados no `ltip_pipeline` porque importar de `rfo_pipeline` puxa o WeasyPrint.
- **Import preguiçoso do WeasyPrint em `rfo_pipeline.gerar_pdf`**, como no LTIP. Assim o DOCX do RFO também fica testável fora do container.
- **`autoescape=True` no `tpl.render` do RFO.** Hoje um `&` ou `<` digitado pelo engenheiro gera XML inválido no DOCX do RFO. O LTIP já usa autoescape, e `test_docx_renderiza_template_versionado` cobre o caso.

## Decisões propostas (para o fechamento de lote)

- **Proposta:** `pontuacao_gut` não é persistida e é calculada no pipeline como G×U×T, a definição clássica da matriz GUT. O `estudo-do-contexto.md` não define a fórmula (só RN-04, para a prioridade); confirmar com o cliente.
- **Proposta:** campos vazios da ficha aparecem como `—` nos dois formatos (o HTML já fazia isso para a maioria).

## Comandos e saídas

Rodados a partir de `04_backend/`. O worktree usa o venv do checkout principal (`../../../../04_backend/.venv`), pois não tem venv próprio.

```text
$ python -m pytest tests/test_ltip_pipeline.py tests/test_ltip_templates.py -rs -q
...........s...........                                                  [100%]
SKIPPED [1] tests\test_ltip_pipeline.py:265: WeasyPrint indisponível nesta máquina (OSError): só carrega no container de 05_infra (GTK/Pango ausentes no Windows).
22 passed, 1 skipped, 1 warning in 4.18s
```

No venv desta máquina, o `import weasyprint` falha com `OSError: [Errno 22] Invalid argument` ao ler `tinycss2/nth.py` (arquivo do venv na pasta do OneDrive), antes de chegar ao GTK. O teste trata `ImportError` e `OSError` como "indisponível" e pula. `pytest.importorskip` não serviria, porque só captura `ImportError`.

```text
$ ruff check --config ../../../../04_backend/ruff.toml app/services/report_generator tests/test_ltip_pipeline.py
All checks passed!

$ ruff check --config ../../../../04_backend/ruff.toml .
Found 111 errors.     # todos preexistentes, nenhum nos arquivos tocados

$ ruff check .
Found 215 errors.     # config resolvida: C:\Users\dynatest\OneDrive - Dynatest Engenharia\pyproject.toml (externo)
```

Sobre o `ruff`: o `04_backend/ruff.toml` do BL-26 (DEC-31/R-11) existe só no checkout principal e **não está versionado** (`git log --all -- 04_backend/ruff.toml` vazio). Sem ele, o worktree volta a resolver o `pyproject.toml` externo do OneDrive, o risco R-11, e as duas configs discordam no isort (first-party `app`). Os arquivos tocados seguem a config do BL-26, no mesmo estilo de `test_ltip_templates.py`. Sob a config externa, sobra 1 `I001` em `tests/test_ltip_pipeline.py`. **Fechamento de lote:** versionar o `ruff.toml`.

Suíte completa:

```text
$ python -m pytest -q
6 failed, 59 passed, 1 skipped, 6 warnings, 91 errors in 105.09s
```

**Os testes de integração não rodaram:** o PostgreSQL de `05_infra/docker-compose.yml` não está no ar (`Test-NetConnection localhost -Port 5433` → `False`), e o `docker` não está no PATH desta sessão. Os 91 erros e as 6 falhas vêm dos testes com banco ou app (`test_auth`, `test_edificacoes`, `test_responsaveis`, `test_seguranca`, `test_visitas`, `test_storage`...), com `ValueError: the greenlet library is required ... No module named 'greenlet._greenlet'` (venv local) e falta de conexão. Nenhum deles importa `app.services.report_generator`. Para rodar no container:

```text
cd 05_infra && docker compose up -d db
cd 04_backend && pytest
```
