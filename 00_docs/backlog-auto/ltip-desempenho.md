---
title: Desempenho do PDF do LTIP — perfil e otimização (T20)
type: gestao
status: concluido
owner: Garra Engenharia
related:
  - 00_docs/backlog-auto/benchmark-pipelines-finais.md
  - 00_docs/backlog-auto/ltip-pipeline.md
  - 00_docs/projeto/decisoes.md
  - 00_docs/projeto/riscos.md
  - 00_docs/estudo-do-contexto.md
tags: [desempenho, rnf-06, r-03, dec-40, ltip, weasyprint, pdf, bl-17, bl-22]
last_updated: 2026-11-04
---

# Desempenho do PDF do LTIP (T20)

> Tarefa T20 · Data: 2026-11-04 · Branch: `worktree-backlog-T20` · Papel: backend.
> Origem: T17 ([benchmark-pipelines-finais.md](benchmark-pipelines-finais.md)), DEC-40 e risco R-03. O LTIP levava 63,2 s (PDF+DOCX) com só 137 páginas e 239 fotos, violando RNF-06.

## Resumo

| Cenário (fotos de 1200 px/q72, 88 KB) | Antes (`8fd7bf9`) | Depois (T20) | Redução |
|---|---|---|---|
| 239 ocorrências / 239 fotos | **72,1 s** · 137 páginas · 397 MB | **11,6 s** · 129 páginas · 286 MB | −84 % (6,2×) |
| 382 ocorrências / 382 fotos (~200 páginas) | **154,5 s** · 209 páginas · 581 MB | **19,3 s** · 201 páginas · 411 MB | −88 % (8,0×) |

Mediana de 3 execuções, cada uma num subprocesso novo, PDF só (o DOCX não mudou). O custo por página do PDF caiu de 0,53–0,74 s para **0,090–0,096 s**, o mesmo patamar do RFO (0,094 s/página na T17). **RNF-06 passa a ser atendido pelo LTIP com folga**, inclusive no cenário de 200 páginas que a T17 não chegou a medir.

Causa: o relatório fotográfico era um **único container `display: flex; flex-wrap: wrap` por sistema**, atravessando dezenas de páginas. A cada página, o WeasyPrint refazia o layout de todas as fichas restantes do sistema. O custo era quadrático no número de fichas por sistema: 72 s → 154 s ao passar de 239 para 382 fichas. A correção põe cada linha de 2 fichas numa tabela fixa própria, com a ficha como célula. Um ganho secundário vem de entregar as fotos ao WeasyPrint direto da memória, sem data URI. A geometria das 120 páginas de fichas ficou idêntica (seção "Aparência").

Efeito colateral visível (correção de defeito): o leiaute antigo deixava o título "7.x. Sistema N" **sozinho numa página** e começava as fichas na página seguinte (8 páginas a mais com 8 sistemas). Agora o título fica na mesma página da primeira linha de fichas, por isso 137 → 129 páginas.

## Ambiente

| Item | Valor |
|---|---|
| Host | Windows 11 Pro, 12 CPUs. Docker Desktop 26.1.4, VM com 7,6 GiB. RAM livre do host ≈ 0,6 GB durante a tarefa |
| Imagem | `garra-bench-t17-backend` (a mesma da T17: python:3.12-slim, **WeasyPrint 70.0**, pydyf 0.13.0, Pillow 10.4.0), via `docker run --rm --memory 2g` com uma cópia de `04_backend/{app,templates,tests}` montada só-leitura em `/app` |
| Serviços | Nenhum. `garra-backend`, `garra-postgres`, `garra-minio` e os containers do Airflow já estavam no ar e **não foram tocados**. O container do bench não usa banco nem MinIO |
| Carga concorrente | T18 e T19 rodavam em paralelo no mesmo host. Por isso o "antes" mediu 72,1 s, contra 62,6 s na T17 (execução única), ou seja, ~15 % de ruído para cima. Antes e depois foram medidos na mesma sessão, com o mesmo script e as mesmas fotos |
| Base | O worktree nasceu em `14ead2f`, sem `ltip_pipeline.py` (o mesmo que aconteceu na T17). O branch foi avançado por fast-forward até `8fd7bf9` (`main` do disparo de T18–T20) antes de qualquer mudança |

O bind mount direto do worktree não funciona: o caminho com "Área" aparece vazio dentro do container. Por isso o código é copiado para `.../jobs/<id>/tmp/bench/backend` antes de cada rodada (`backend_antes` = arquivos de `HEAD`).

## Dados sintéticos

São o mesmo gerador e o mesmo contexto da T17 (Apêndice A de `benchmark-pipelines-finais.md`), reduzidos ao LTIP no script `bench_ltip.py` (Apêndice A deste Doc):

- foto `_foto(i)`: 2000×1500 q85 com textura e ruído, reduzida por `rfo_pipeline.otimizar_imagem` (1200 px, q72). Com 239 fotos, 20,6 MB e 88,1 KB em média, idêntico à T17. Com 382 fotos, 33,0 MB e 88,3 KB;
- contexto `ltip`: n ocorrências, 8 sistemas, 5 subsistemas, ficha GUT completa, `descricao` = parágrafo LOREM de 290 caracteres, 1 foto por ocorrência e 3 parágrafos por seção de texto.

Nada foi lido de `01_output-context/`.

## Perfil (antes)

### Fases (n = 239, `bench_ltip.py fases`)

| Fase | s | % |
|---|---|---|
| Jinja2 + base64 (`renderizar_html`) | 0,26 | 0,3 |
| `HTML(string=…)` (parse de 27,8 MB de HTML) | 2,67 | 3,5 |
| `render()`: cascata CSS (`get_all_computed_styles`) | 2,03 | 2,7 |
| `render()`: árvore de caixas (`build_formatting_structure`, inclui decodificar as imagens) | 1,96 | 2,6 |
| `render()`: **layout/paginação** (restante de `render()`) | **66,6** | **87** |
| `write_pdf()` (desenho + serialização, 21 MB) | 2,58 | 3,4 |

### cProfile (n = 239, `bench_ltip.py perfil`; com o overhead do profiler o total sobe para 152 s)

```text
   ncalls  tottime  cumtime  função
      137    0.041  133.328  page.py:559(make_page)
      128    0.641  132.660  flex.py:18(flex_layout)            <- 8 sistemas, 128 layouts de flex (1 por página)
     4543    2.898  116.388  table.py:80(group_layout)          <- 239 fichas, 4.543 layouts de tabela (~19 por ficha)
   205076    3.798   88.270  inline.py:56(get_next_linebox)     <- 205 mil line boxes para ~11 mil linhas reais
   454280   13.325   13.326  line_break.py:134(get_first_line)  (Pango)
  6979337    6.742   13.273  percent.py:28(resolve_one_percentage)
```

Leitura: o `flex_layout` de cada sistema é chamado uma vez por página e, a cada chamada, refaz o layout da tabela de todas as fichas que ainda faltam. As fichas são 239, mas a tabela de ficha é diagramada 4.543 vezes. Os demais custos (Pango, percentuais, line boxes) só crescem por causa dessa repetição.

### cProfile depois (mesmo cenário)

```text
   ncalls  tottime  cumtime  função
      129    0.031    9.997  page.py:559(make_page)
  471/232    0.128    9.328  table.py:80(group_layout)          <- 232 tabelas-linha + 239 tabelas de ficha
```

Não há mais `flex_layout`. Cada ficha é diagramada uma vez, e cada linha duas: uma tentativa na página onde não cabe, que vai para a seguinte por `page-break-inside: avoid`, e a definitiva. Total sob profiler: 27 s, contra 152 s antes.

## Hipóteses

Variantes do template aplicadas em memória pelo `bench_ltip.py variantes`, com o HTML e as fotos idênticos e só o template alterado. Cada número é uma execução de `HTML().render()` + `write_pdf()`.

**n = 60 (triagem):**

| Variante | O que muda | render (s) | Páginas | Resultado |
|---|---|---|---|---|
| `base` | template de `HEAD` | 7,14 | 49 | referência |
| `sem_avoid` | remove `page-break-inside: avoid` da ficha | 6,63 | 49 | sem ganho relevante |
| `bloco_inline` | fichas `inline-block`, sem flex | 6,22 | **77** | quebra o leiaute (descartada) |
| `grid` | `display: grid` de 2 colunas | **9,95** | 41 | mais lento que o flex |
| `pares_flex` | um flex pequeno por par de fichas | 5,18 | 41 | geometria idêntica |
| `pares_tabela` (v1) | par em `<table>` com a ficha dentro do `td` | 3,57 | 41 | ficha com metade da largura (descartada) |
| `sem_fotos` | sem `<img>` (diagnóstico) | 8,23 | 49 | fotos não pesam no layout |
| `sem_rodape` | sem `@bottom-center` (diagnóstico) | 7,48 | 49 | rodapé não pesa |
| `sem_bordas` | sem bordas e sem fundo cinza (diagnóstico) | 8,71 | 49 | bordas não pesam |
| `sem_tabela` | troca a tabela da ficha por um `<p>` (diagnóstico) | 2,65 | 33 | a tabela da ficha é o item caro, por repetição |

**n = 239 (cenário da T17):**

| Variante | parse (s) | render (s) | write_pdf (s) | Páginas | RSS pico (MB) |
|---|---|---|---|---|---|
| `base` (fases) | 2,67 | 70,62 | 2,58 | 137 | 397 |
| `sem_avoid` | 2,58 | 66,60 | 3,01 | 137 | 376 |
| `pares_flex` (2 execuções) | 2,07 / 2,61 | 23,35 / 19,41 | 2,73 / 3,23 | 129 | 377 |
| `pares_flex_quebra` (+ `page-break-before` por linha) | 2,52 | 18,07 | 2,97 | 129 | 377 |
| **`pares_tabela2`** (2 execuções) | 2,51 / 2,33 | **11,94 / 8,87** | 2,83 / 2,44 | 129 | 382 |
| `pares_tabela2_quebra` | 2,53 | 13,66 | 3,12 | 129 | 382 |
| **`pares_tabela2_fetch`** (fotos via `url_fetcher`) | **0,28** | 9,13 | 2,09 | 129 | **286** |

| Hipótese do enunciado | Veredito | Evidência |
|---|---|---|
| Fichas em flex atravessando páginas (vs tabela/grid) | ✅ **confirmada (causa principal)** | 128 `flex_layout` e 4.543 `table_layout` para 239 fichas. `pares_tabela2` reduz o render de 70,6 s para 8,9–11,9 s. O grid é pior que o flex (9,95 contra 7,14 s com n = 60) |
| `page-break-inside: avoid` em tabelas aninhadas | ❌ descartada | `sem_avoid`: 66,6 s contra 70,6 s (dentro do ruído), mesma paginação |
| `position: running()` de cabeçalho/rodapé | ❌ descartada | O template não usa `running()` (0 ocorrências). O rodapé é `@bottom-center`/`@bottom-right`, e `sem_rodape` não muda o tempo |
| `box-shadow` / `border-radius` | ❌ descartada | 0 ocorrências no template. `sem_bordas`, sem bordas nem fundos, também não muda o tempo |
| SVG da marca repetido por página | ❌ descartada | `logo_data_uri` aparece só na capa (1 vez no documento) |
| Imagens em data URI | ⚠️ confirmada só para parse e memória | Não pesam no layout (`sem_fotos`). O parse de 27,8 MB de base64 custa 2,0–2,4 s e ~95 MB de RSS. Com `url_fetcher`, o parse vai a 0,28 s e o RSS de 382 a 286 MB |
| CSS universal | ❌ descartada | Não há seletor `*`. A cascata inteira custa 2,0 s (2,7 %) |
| Forçar 1 linha por página (`page-break-before`) para evitar a tentativa dupla | ❌ descartada | `pares_flex_quebra` 18,1 s e `pares_tabela2_quebra` 13,7 s: sem ganho e com mudança de regra |

## Mudanças

| Arquivo:linha | Mudança |
|---|---|
| `04_backend/app/scripts/build_ltip_templates.py:59` | `VAO_FICHAS_CM = 0.4`, o espaço entre fichas (era o `gap: 0.4cm` do flex) |
| `04_backend/app/scripts/build_ltip_templates.py:82` | `por_linha = fichas_por_pagina` do `layout.json` (2), também usado no `batch` |
| `04_backend/app/scripts/build_ltip_templates.py:147-157` | CSS: `.fichas { display: flex }` dá lugar a `table.fichas { table-layout: fixed; border-collapse: separate; border-spacing: 0; margin-bottom: 0.4cm; page-break-inside: avoid }`, com `td.vao` (0,4 cm), `td.ficha-vazia` (48 %) e `td.resto`. `.ficha` vira célula (`padding: 0; vertical-align: top`) e mantém `width: 48%`, a borda de 0,5 pt e o `avoid` |
| `04_backend/app/scripts/build_ltip_templates.py:196-222` | HTML: `{% for linha in sistema.ocorrencias\|batch(2) %}<table class="fichas"><tr>`, com cada ficha num `<td class="ficha">`, vão entre fichas e preenchimento da linha incompleta. A variável da foto passa de `foto_data_uri` a `foto_src` |
| `04_backend/templates/ltip/ltip_template.html.j2:55-65, 127-153` | Regerado por `python -m app.scripts.build_ltip_templates`. **`layout.json` e `ltip_template.docx` não mudaram**: o DOCX regerado tinha todas as partes do zip byte a byte iguais (só o timestamp do contêiner diferia), então o arquivo versionado foi mantido |
| `04_backend/app/services/report_generator/ltip_pipeline.py:79` | `ESQUEMA_FOTO = "garra-foto:"` |
| `04_backend/app/services/report_generator/ltip_pipeline.py:209-238` | `_renderizar(contexto, fotos_bytes, fotos_em_memoria)`: põe o data URI em `foto_src` (`renderizar_html`, que mantém o HTML autocontido) ou `garra-foto:<índice>` com a foto anexada à lista |
| `04_backend/app/services/report_generator/ltip_pipeline.py:241-261` | `_fetcher_de_fotos`: subclasse de `weasyprint.urls.URLFetcher` que serve `garra-foto:<i>` da memória e repassa o resto (o logo) ao fetcher padrão. Se a classe não existir, devolve `None` e o PDF volta aos data URIs |
| `04_backend/app/services/report_generator/ltip_pipeline.py:273-280` | `gerar_pdf` usa o fetcher. As métricas devolvidas continuam as mesmas |
| `04_backend/tests/test_ltip_pipeline.py:192-214` | Testes novos: `test_html_agrupa_fichas_em_linhas_de_duas` (3 linhas, 2 preenchimentos, ordem RN-11, sem flex) e `test_html_do_pdf_serve_as_fotos_da_memoria` (sem base64, índice correto) |
| `04_backend/tests/test_ltip_pipeline.py:305-325` | `test_pdf_gerado_com_weasyprint` passou a conferir, com o pdfplumber, que as 3 fotos chegaram ao PDF e que 01 e 02 ficam lado a lado com a mesma largura. Teste novo `test_fetcher_entrega_a_foto_da_memoria` |
| `04_backend/tests/test_ltip_templates.py:217-232` | A asserção de iteração passa a esperar `batch(`/`for ocorrencia in linha`. Teste novo `test_html_gerado_agrupa_fichas_em_linhas_sem_flex` |

O pipeline de nenhum outro tipo de relatório foi alterado, e `01_output-context/` não foi tocado.

Ponto de atenção: o `url_fetcher` como função (API antiga) **quebra no WeasyPrint 70** (`AttributeError: 'function' object has no attribute '_fail_on_errors'`, visto no bench). Por isso o código usa a classe `URLFetcher`, com o fallback para data URI. `requirements.txt` exige `weasyprint>=69.0` sem teto. O caminho de fallback não foi exercitado, porque só há WeasyPrint 70 disponível.

## Aparência

Comparação feita por `comparar_fichas.py` (Apêndice B) entre o PDF de `HEAD` e o de T20, n = 239. As páginas são casadas pelo primeiro rótulo "Foto nº NN". Em cada página entram as caixas das fotos, a posição de todas as palavras, os retângulos (fundos `#D9D9D9`) e as linhas e curvas (bordas), com tolerância de 0,15 pt e sem o número da página no rodapé:

```text
{"paginas_a": 137, "paginas_b": 129, "paginas_de_fichas_comparadas": 120, "identicas": 120,
 "identicas_com_deslocamento_vertical": 8, "diferentes": 0, "exemplos": []}
```

- As **120 páginas de fichas são idênticas**: fotos de 231×173 pt em x = 57 e x = 301, as mesmas bordas, fundos, fontes e quebras de linha, e 2 fichas por página.
- Em 8 delas (a primeira página de cada sistema) tudo desce 33,4 pt, porque o título "7.x" agora está acima da primeira linha em vez de sozinho na página anterior.
- Margens, rodapé, capa e capítulos não mudaram (o CSS deles é o mesmo). A ordem RN-11 continua a mesma, porque `batch` preserva a ordem de `sistema.ocorrencias`.
- As fichas de uma linha continuam com a mesma altura: antes vinha do `align-items: stretch` do flex, agora da célula de tabela. Com fichas de alturas diferentes, a borda de ambas segue a mais alta, como antes.
- Diferença conhecida: o espaço de 0,4 cm entre linhas era `row-gap` do flex e agora é `margin-bottom` da tabela-linha. Dentro da página dá o mesmo espaçamento. Como só cabe uma linha por página com dados reais, isso não aparece nos PDFs medidos.

## Antes/depois (detalhe)

| n | Versão | Páginas | Mediana (s) | mín–máx (s) | `conversao_pdf` mediana (s) | `render_html` (s) | RSS pico (MB) | PDF (MB) | s/página |
|---|---|---|---|---|---|---|---|---|---|
| 239 | antes | 137 | **72,13** | 71,45–74,52 | 71,73 | 0,25–0,35 | 397 | 21,1 | 0,526 |
| 239 | depois | 129 | **11,57** | 11,31–12,60 | 11,47 | 0,07–0,08 | 286 | 21,1 | 0,090 |
| 382 | antes | 209 | **154,51** | 153,78–159,83 | 153,85 | 0,32–0,60 | 581 | 33,7 | 0,739 |
| 382 | depois | 201 | **19,30** | 18,72–21,07 | 19,18 | 0,09–0,11 | 411 | 33,7 | 0,096 |

Job completo estimado para RNF-06 (< 60 s), somando o DOCX medido na T17 e o I/O de 2026-08-05:

| Cenário | PDF (T20) | DOCX (T17) | MinIO + registro (2026-08-05) | Total estimado |
|---|---|---|---|---|
| 239 fotos / 129 p. | 11,6 | 0,6 (sem foto) a 2,1 (com foto) | 11,2 | **~23–25 s** ✅ |
| 382 fotos / 201 p. | 19,3 | ~3,4 (extrapolado de 2,1 s/239 fotos) | ~18 (extrapolado) | **~41 s** ✅ |

## O que continua aberto

- **Nada do LTIP fica acima do limite de RNF-06** nos cenários medidos. O PDF de 200 páginas leva 19,3 s.
- **RSS de 411 MB no PDF de 200 páginas**: continua valendo a recomendação da T17 de dimensionar o worker com ≥ 1 GB se PDF e DOCX rodarem em paralelo.
- **DOCX do LTIP ainda sem foto**: o template versionado não tem `{{ ocorrencia.foto }}` (lacuna de BL-17, `ltip-pipeline.md`). Ficou fora do escopo, porque mudaria o DOCX. Quando entrar, o custo esperado é de ~2 s para 239 fotos (T17).
- **Vistoria Residencial** (0,243 s/página, 5 % de margem na T17) não foi tocada. Ela não usa flex único por seção, então a causa encontrada aqui não se aplica diretamente.
- O RFO também usa `.fotos { display: flex; flex-wrap: wrap }`, mas com 3 fotos por visita e uma visita por página. O container é pequeno e não atravessa páginas, por isso o RFO não sofre o efeito quadrático (0,094 s/página na T17).
- O fallback para data URI quando o WeasyPrint não tem `URLFetcher` não foi testado (só há a 70.0 no container).
- **Suíte completa do backend não validada contra o banco** (seção "Testes").

## Propostas de decisão (só neste Doc; o registro em `decisoes.md` fica para o fechamento de lote)

- **Proposta DEC-T20-a**: nos templates WeasyPrint, conteúdo repetitivo que atravessa várias páginas (fichas, fotos, figuras) não deve ficar num único container `display: flex` ou `grid`. Cada linha vira um bloco pequeno (tabela fixa ou flex por linha) com `page-break-inside: avoid`. Motivo: custo quadrático no WeasyPrint 70, medido aqui em 72 → 11,6 s e 154 → 19,3 s.
- **Proposta DEC-T20-b**: os pipelines PDF entregam as fotos ao WeasyPrint por `url_fetcher` (classe `URLFetcher`), não por data URI, e `renderizar_html` continua autocontido para testes e pré-visualização. Hoje isso está só no LTIP. Estender aos outros pipelines economizaria ~2 s e ~100 MB por 240 fotos, mas fica para tarefa própria. Junto, fixar o piso `weasyprint>=70` em `requirements.txt` ou manter o fallback.
- Para o fechamento: com estes números, **R-03 e DEC-40 podem registrar o LTIP como atendendo RNF-06**.

## Testes

Rodados a partir de `04_backend/`.

**Windows (`.venv` do repositório; os testes de PDF são pulados porque o WeasyPrint não carrega):**

```text
$ python -m pytest -q tests/test_ltip_pipeline.py tests/test_ltip_templates.py -p no:cacheprovider
25 passed, 2 skipped, 1 warning in 5.57s
```

**Container (`garra-bench-t17-backend`, WeasyPrint 70.0; inclui os testes de PDF e do fetcher):**

```text
$ python -m pytest -q -p no:cacheprovider tests/test_ltip_pipeline.py tests/test_ltip_templates.py
27 passed, 1 warning in 3.63s
```

O aviso é o `DeprecationWarning` de HarfBuzz-Subset do WeasyPrint.

**ruff** (o `.venv` não tem ruff; foi usado o do Anaconda, como na T17):

```text
$ ruff --version && ruff check . --output-format concise
ruff 0.15.1
app\repositories\ocorrencia_repository.py:25:25: F821 Undefined name `Inspecao`
app\repositories\ocorrencia_repository.py:28:67: F821 Undefined name `SistemaPredial`
app\repositories\ocorrencia_repository.py:29:25: F821 Undefined name `SistemaPredial`
app\repositories\ocorrencia_repository.py:32:73: F821 Undefined name `Subsistema`
app\repositories\ocorrencia_repository.py:33:25: F821 Undefined name `Subsistema`
app\scripts\vistoria_cautelar_layout_extractor.py:81:56: RUF001 String contains ambiguous `–` (EN DASH). Did you mean `-` (HYPHEN-MINUS)?
app\scripts\vistoria_cautelar_layout_extractor.py:86:44: RUF001 String contains ambiguous `–` (EN DASH). Did you mean `-` (HYPHEN-MINUS)?
tests\test_fotos_lacunas.py:11:1: I001 [*] Import block is un-sorted or un-formatted
tests\test_ocorrencias_regras.py:6:1: I001 [*] Import block is un-sorted or un-formatted
tests\test_visitas_lacunas.py:7:1: I001 [*] Import block is un-sorted or un-formatted
tests\test_vistoria_cautelar_pipeline.py:133:40: RUF043 Pattern passed to `match=` contains metacharacters but is neither escaped nor raw
tests\test_vistoria_cautelar_pipeline.py:163:40: RUF043 Pattern passed to `match=` contains metacharacters but is neither escaped nor raw
tests\test_vistoria_cautelar_templates.py:11:1: I001 [*] Import block is un-sorted or un-formatted
tests\test_vistoria_cautelar_templates.py:219:22: RUF005 Consider iterable unpacking instead of concatenation
tests\test_vistoria_cautelar_templates.py:228:15: RUF005 Consider iterable unpacking instead of concatenation
tests\test_vistoria_cautelar_templates.py:290:20: RUF005 Consider iterable unpacking instead of concatenation
Found 16 errors.
```

**Nenhum dos 16 achados está em arquivo tocado por esta tarefa**, e todos já existiam em `8fd7bf9`. São os 14 que a T17 registrou mais dois `I001`, em `test_fotos_lacunas.py` e `test_visitas_lacunas.py`, que vieram de T15/T16. Os `F821` de `ocorrencia_repository.py` continuam parecendo bug real e ficam para o integrador.

**Suíte completa (`pytest` sem filtro, Windows):**

```text
$ python -m pytest -q -p no:cacheprovider
8 failed, 128 passed, 6 skipped, 6 warnings, 181 errors in 181.90s (0:03:01)
```

As 181 errors e as 8 falhas são todas de testes de integração com banco ou app, em arquivos que esta tarefa não tocou: `test_auth`, `test_contratos`, `test_edificacoes`, `test_fotos*`, `test_gabarito`, `test_models`, `test_ocorrencias_*`, `test_portal_cliente`, `test_rbac_*`, `test_responsaveis`, `test_seguranca`, `test_storage`, `test_visitas*`. Têm duas causas de ambiente:

- `ValueError: the greenlet library is required to use this function. No module named 'greenlet._greenlet'`: o `greenlet` do `.venv` está quebrado e o SQLAlchemy async falha antes de conectar;
- `OSError: [Errno 22] Invalid argument` num import a partir do caminho do OneDrive.

O PostgreSQL de `05_infra` estava no ar (`garra-postgres`, `127.0.0.1:5433`), mas a suíte **não foi apontada para ele**. O worktree não tem `.env`, então as configurações padrão apontam para `localhost:5432` com senha vazia. O único banco em 5433 é o `garra_engenharia` de desenvolvimento, usado pelo `garra-backend` no ar, e os testes de integração gravam nele (Regra de pronto, item 4). Portanto **a suíte completa contra o PostgreSQL não rodou**: as mudanças desta tarefa não tocam código de banco, e os 27 testes do LTIP passam no container. `npm run lint`/`build` não se aplicam (nada em `03_frontend/`).

## Como reproduzir

```powershell
# run.ps1 (Apêndice C) monta $PSScriptRoot\backend (ou $env:BENCH_APP) em /app e o diretório do bench em /bench.
# Cópia do código: app/, templates/, tests/, pytest.ini, conftest.py de 04_backend/ para <bench>\backend.
# Para o "antes": <bench>\backend_antes com ltip_pipeline.py e ltip_template.html.j2 de HEAD (git show HEAD:...).

.\run.ps1 "python /bench/bench_ltip.py fotos --n 382"                                  # gera 0000..0381.jpg (1200 px/q72)
$env:BENCH_APP='backend_antes'; .\run.ps1 "python /bench/bench_ltip.py medir --reps 3 --n 239 --rotulo antes"
$env:BENCH_APP='backend_antes'; .\run.ps1 "python /bench/bench_ltip.py medir --reps 3 --n 382 --rotulo antes"
$env:BENCH_APP='';              .\run.ps1 "python /bench/bench_ltip.py medir --reps 3 --n 239 --rotulo depois"
$env:BENCH_APP='';              .\run.ps1 "python /bench/bench_ltip.py medir --reps 3 --n 382 --rotulo depois"
.\run.ps1 "python /bench/bench_ltip.py fases --n 239"                                   # fases (no código montado)
.\run.ps1 "python /bench/bench_ltip.py perfil --n 239 --top 40"                         # cProfile
.\run.ps1 "python /bench/bench_ltip.py variantes --n 239 base sem_avoid pares_flex pares_tabela2 pares_tabela2_fetch"
.\run.ps1 "python /bench/comparar_fichas.py /bench/pdfs/ltip_antes_239.pdf /bench/pdfs/ltip_depois_239.pdf"
.\run.ps1 "cp -r /app /tmp/app && cd /tmp/app && python -m pytest -q -p no:cacheprovider tests/test_ltip_pipeline.py tests/test_ltip_templates.py"
```

Na tarefa, o "antes" de n = 239 rodou com o código montado antes das mudanças. O `backend_antes` foi criado depois, para n = 382.

Saída bruta (`bruto.jsonl`):

```text
{"rep": 1, "rotulo": "antes", "n": 239, "parede_s": 72.125, "rss_pico_mb": 396.8, "render_html": 0.346, "conversao_pdf": 71.729, "n_paginas": 137, "tamanho_bytes": 22081765}
{"rep": 2, "rotulo": "antes", "n": 239, "parede_s": 74.523, "rss_pico_mb": 396.8, "render_html": 0.248, "conversao_pdf": 74.241, "n_paginas": 137, "tamanho_bytes": 22081763}
{"rep": 3, "rotulo": "antes", "n": 239, "parede_s": 71.449, "rss_pico_mb": 396.3, "render_html": 0.33, "conversao_pdf": 71.064, "n_paginas": 137, "tamanho_bytes": 22081762}
{"rep": 1, "rotulo": "depois", "n": 239, "parede_s": 12.596, "rss_pico_mb": 285.6, "render_html": 0.083, "conversao_pdf": 12.48, "n_paginas": 129, "tamanho_bytes": 22077645}
{"rep": 2, "rotulo": "depois", "n": 239, "parede_s": 11.571, "rss_pico_mb": 285.5, "render_html": 0.068, "conversao_pdf": 11.473, "n_paginas": 129, "tamanho_bytes": 22077650}
{"rep": 3, "rotulo": "depois", "n": 239, "parede_s": 11.308, "rss_pico_mb": 285.5, "render_html": 0.067, "conversao_pdf": 11.207, "n_paginas": 129, "tamanho_bytes": 22077652}
{"rep": 1, "rotulo": "depois", "n": 382, "parede_s": 19.304, "rss_pico_mb": 411.5, "render_html": 0.09, "conversao_pdf": 19.176, "n_paginas": 201, "tamanho_bytes": 35340928}
{"rep": 2, "rotulo": "depois", "n": 382, "parede_s": 21.069, "rss_pico_mb": 411.2, "render_html": 0.1, "conversao_pdf": 20.906, "n_paginas": 201, "tamanho_bytes": 35340934}
{"rep": 3, "rotulo": "depois", "n": 382, "parede_s": 18.72, "rss_pico_mb": 411.2, "render_html": 0.105, "conversao_pdf": 18.561, "n_paginas": 201, "tamanho_bytes": 35340928}
{"rep": 1, "rotulo": "antes", "n": 382, "parede_s": 154.512, "rss_pico_mb": 583.0, "render_html": 0.604, "conversao_pdf": 153.846, "n_paginas": 209, "tamanho_bytes": 35345502}
{"rep": 2, "rotulo": "antes", "n": 382, "parede_s": 153.776, "rss_pico_mb": 581.1, "render_html": 0.322, "conversao_pdf": 153.42, "n_paginas": 209, "tamanho_bytes": 35345504}
{"rep": 3, "rotulo": "antes", "n": 382, "parede_s": 159.833, "rss_pico_mb": 581.0, "render_html": 0.341, "conversao_pdf": 159.429, "n_paginas": 209, "tamanho_bytes": 35345502}
```

Os scripts ficam fora do Git, no diretório temporário do job, e estão transcritos abaixo.

## Apêndice A — `bench_ltip.py` (integral, fora do Git)

```python
"""Benchmark e perfil do PDF do LTIP (T20, RNF-06/DEC-40).

Mesmo gerador de dados sintéticos de bench_pipelines.py (T17, Apêndice A de
00_docs/backlog-auto/benchmark-pipelines-finais.md), reduzido ao LTIP, mais
perfil (cProfile + fases do WeasyPrint), variantes de template e comparação de
geometria entre PDFs. Roda DENTRO do container (WeasyPrint), com o código em
/app e este script + fotos em /bench:

    python /bench/bench_ltip.py fotos --n 239
    python /bench/bench_ltip.py medir --reps 3 --n 239 --rotulo antes
    python /bench/bench_ltip.py fases --n 239
    python /bench/bench_ltip.py perfil --n 239
    python /bench/bench_ltip.py variantes --n 60 base sem_avoid ...
    python /bench/bench_ltip.py comparar /tmp/saida/a.pdf /tmp/saida/b.pdf

Só dados sintéticos; nada de 01_output-context/.
"""
from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
import random
import re
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app")
BENCH = Path("/bench")
FOTOS = BENCH / "fotos" / "otimizado"
SAIDA = Path("/tmp/saida")
LOREM = (
    "Constatou-se, durante a vistoria, a presença de fissuras de pequena abertura no revestimento "
    "argamassado, com indícios de infiltração por capilaridade junto ao rodapé e manchas de umidade. "
    "Recomenda-se o acompanhamento da evolução e a correção conforme a NBR 13749 e a NBR 16747."
)


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _foto(indice: int) -> bytes:
    """Idêntica à de T17: 2000x1500 q85 com textura/ruído (depois reduzida a 1200 px/q72)."""
    from PIL import Image, ImageDraw, ImageFilter

    rnd = random.Random(indice)
    w, h = 2000, 1500
    base = Image.linear_gradient("L").resize((w, h)).convert("RGB")
    cor = Image.new("RGB", (w, h), (rnd.randint(60, 200), rnd.randint(60, 200), rnd.randint(60, 200)))
    img = Image.blend(base, cor, 0.6)
    d = ImageDraw.Draw(img)
    for _ in range(40):
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        d.ellipse([x, y, x + rnd.randint(40, 400), y + rnd.randint(40, 300)],
                  fill=tuple(rnd.randint(0, 255) for _ in range(3)))
    for _ in range(25):
        d.line([(rnd.randint(0, w), rnd.randint(0, h)), (rnd.randint(0, w), rnd.randint(0, h))],
               fill=(30, 30, 30), width=rnd.randint(1, 4))
    ruido = Image.effect_noise((w, h), 28).convert("RGB")
    img = Image.blend(img.filter(ImageFilter.GaussianBlur(1.2)), ruido, 0.22)
    d = ImageDraw.Draw(img)
    d.text((30, 30), f"Foto sintetica #{indice}", fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def cmd_fotos(n: int) -> None:
    from app.services.report_generator.rfo_pipeline import otimizar_imagem

    FOTOS.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        alvo = FOTOS / f"{i:04d}.jpg"
        if not alvo.exists():
            alvo.write_bytes(otimizar_imagem(_foto(i)))  # 1200 px / q72, como em T17
    tam = [p.stat().st_size for p in FOTOS.glob("*.jpg")]
    print(json.dumps({"n": len(tam), "media_kb": round(statistics.mean(tam) / 1024, 1),
                      "total_mb": round(sum(tam) / 2**20, 1)}))


def contexto(n: int) -> tuple[dict, dict[str, bytes]]:
    """Mesmo contexto 'ltip' de T17: n ocorrências, 8 sistemas, 5 subsistemas, 1 foto cada."""
    sistemas = [f"Sistema {i + 1}" for i in range(8)]
    keys = [f"{i:04d}.jpg" for i in range(n)]
    ctx = {
        "edificacao": {"nome": "Condomínio Sintético"}, "fiscal": {"nome": "Eng. Sintético", "crea": "0/D-XX"},
        "contrato": {"art_fiscalizacao": "ART-0001"}, "data_emissao": "2026-11-04",
        **{f"{s}_paragrafos": [LOREM] * 3 for s in ("introducao", "objetivo", "objeto", "metodologia",
                                                     "documentacao_analisada", "consideracoes_preliminares",
                                                     "conclusao")},
        "ocorrencias": [
            {"seq_numero": i + 1, "sistema": sistemas[i % 8], "sistema_ordem": i % 8,
             "subsistema": f"Subsistema {i % 5}", "subsistema_ordem": i % 5, "situacao": "Não conforme",
             "classificacao": "Anomalia", "tipo_anomalia": "Endógena", "grau_risco": "MEDIO",
             "prioridade": 3, "gut_gravidade": 3.0, "gut_urgencia": 3.0, "gut_tendencia": 2.0,
             "localizacao": f"Pavimento {i % 12}", "descricao": LOREM, "recomendacao": LOREM[:160],
             "fotos": [{"storage_key": keys[i]}]}
            for i in range(n)
        ],
    }
    return ctx, {k: (FOTOS / k).read_bytes() for k in keys}


# --- medição (subprocesso novo, como em T17) ------------------------------------


def cmd_uma(n: int, rotulo: str) -> None:
    from app.services.report_generator import ltip_pipeline as p
    import weasyprint  # noqa: F401  (aquecido, como num worker)

    ctx, fotos = contexto(n)
    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / f"ltip_{rotulo}_{n}.pdf"
    rss0 = _rss_mb()
    t0 = time.perf_counter()
    m = p.gerar_pdf(ctx, fotos, destino)
    parede = time.perf_counter() - t0
    print(json.dumps({"rotulo": rotulo, "n": n, "n_fotos": len(fotos),
                      "fotos_mb": round(sum(map(len, fotos.values())) / 2**20, 1),
                      "parede_s": round(parede, 3), "rss_antes_mb": round(rss0, 1),
                      "rss_pico_mb": round(_rss_mb(), 1),
                      **{c: (round(v, 3) if isinstance(v, float) else v) for c, v in m.items()}}))


def cmd_medir(reps: int, n: int, rotulo: str) -> None:
    linhas = []
    with (BENCH / "bruto.jsonl").open("a", encoding="utf-8") as bruto:
        for rep in range(1, reps + 1):
            out = subprocess.run([sys.executable, __file__, "uma", str(n), rotulo],
                                 capture_output=True, text=True, check=True)
            r = {"rep": rep, **json.loads(out.stdout.strip().splitlines()[-1])}
            bruto.write(json.dumps(r) + "\n")
            bruto.flush()
            print(json.dumps(r), flush=True)
            linhas.append(r)
    t = [r["parede_s"] for r in linhas]
    c = [r["conversao_pdf"] for r in linhas]
    print(json.dumps({"rotulo": rotulo, "n": n, "paginas": linhas[0]["n_paginas"],
                      "mediana_s": statistics.median(t), "min_s": min(t), "max_s": max(t),
                      "conversao_mediana_s": statistics.median(c),
                      "rss_pico_mediano_mb": statistics.median(r["rss_pico_mb"] for r in linhas),
                      "tamanho_mb": round(linhas[0]["tamanho_bytes"] / 2**20, 1)}))


# --- fases do WeasyPrint e cProfile ---------------------------------------------


FETCH: dict[str, bytes] = {}


def _fetcher():
    from weasyprint.urls import URLFetcher, URLFetcherResponse

    class Fotos(URLFetcher):
        def fetch(self, url, headers=None):
            if url.startswith("garra-foto:"):
                return URLFetcherResponse(url, FETCH[url[len("garra-foto:"):]], {"Content-Type": "image/jpeg"})
            return super().fetch(url, headers)
    return Fotos()


def _fases(html_str: str, destino: Path) -> dict:
    from weasyprint import HTML
    from weasyprint.css import get_all_computed_styles  # noqa: F401  (só para garantir a versão)

    t0 = time.perf_counter()
    extra = {"url_fetcher": _fetcher()} if FETCH else {}
    doc_html = HTML(string=html_str, base_url="/app/templates", **extra)
    t1 = time.perf_counter()
    documento = doc_html.render()
    t2 = time.perf_counter()
    documento.write_pdf(str(destino))
    t3 = time.perf_counter()
    return {"parse_html_s": round(t1 - t0, 3), "render_s": round(t2 - t1, 3),
            "write_pdf_s": round(t3 - t2, 3), "paginas": len(documento.pages)}


def cmd_fases(n: int) -> None:
    """Fases + quebra de render() em cascata CSS x layout via monkeypatch."""
    import weasyprint.document as wdoc
    from app.services.report_generator import ltip_pipeline as p

    tempos: dict[str, float] = {}

    def cronometrar(modulo, nome):
        original = getattr(modulo, nome)

        def wrapper(*a, **k):
            t = time.perf_counter()
            try:
                return original(*a, **k)
            finally:
                tempos[nome] = tempos.get(nome, 0.0) + time.perf_counter() - t
        setattr(modulo, nome, wrapper)

    for nome in ("get_all_computed_styles", "build_formatting_structure", "layout_document"):
        if hasattr(wdoc, nome):
            cronometrar(wdoc, nome)
    ctx, fotos = contexto(n)
    t = time.perf_counter()
    html_str = p.renderizar_html(ctx, fotos)
    jinja = time.perf_counter() - t
    SAIDA.mkdir(exist_ok=True)
    r = _fases(html_str, SAIDA / "fases.pdf")
    print(json.dumps({"n": n, "jinja_s": round(jinja, 3), "html_mb": round(len(html_str) / 2**20, 1), **r,
                      **{f"render.{k}_s": round(v, 3) for k, v in tempos.items()}}))


def cmd_perfil(n: int, top: int, variante: str | None = None) -> None:
    from app.services.report_generator import ltip_pipeline as p

    if variante:
        html_str = _render_variante(variante, n)
    else:
        ctx, fotos = contexto(n)
        html_str = p.renderizar_html(ctx, fotos)
    SAIDA.mkdir(exist_ok=True)
    prof = cProfile.Profile()
    prof.enable()
    r = _fases(html_str, SAIDA / "perfil.pdf")
    prof.disable()
    print(json.dumps({"n": n, **r}))
    st = pstats.Stats(prof)
    st.strip_dirs().sort_stats("cumulative").print_stats(top)
    st.sort_stats("tottime").print_stats(top)


# --- variantes de template (hipóteses) ------------------------------------------


def _css(src: str, seletor: str, novo: str) -> str:
    padrao = re.compile(r"^  " + re.escape(seletor) + r" \{[^}]*\}", re.M)
    assert padrao.search(src), seletor
    return padrao.sub(lambda _m: f"  {seletor} {{ {novo} }}", src, count=1)


FICHA_LOOP_INI = "{% for ocorrencia in sistema.ocorrencias %}"


def _pares(src: str, abre: str, fecha: str, abre_cel: str = "", fecha_cel: str = "") -> str:
    """Agrupa as fichas em linhas de duas: um container pequeno por par."""
    src = src.replace(
        FICHA_LOOP_INI,
        "{% for par in sistema.ocorrencias|batch(2) %}" + abre + "{% for ocorrencia in par %}" + abre_cel, 1)
    i = src.index("{% endfor %}", src.index("{% for par in"))
    return src[:i] + fecha_cel + "{% endfor %}" + fecha + "{% endfor %}" + src[i + len("{% endfor %}"):]


VARIANTES = {
    "base": lambda s: s,
    # H1: flex único atravessando dezenas de páginas
    "sem_avoid": lambda s: s.replace("page-break-inside: avoid; ", ""),
    "bloco_inline": lambda s: _css(_css(s, ".fichas", ""), ".ficha",
                                   "display: inline-block; vertical-align: top; width: 48.0%; margin-right: 0.4cm; "
                                   "margin-bottom: 0.4cm; page-break-inside: avoid; border: 0.5pt solid #999;"),
    "grid": lambda s: _css(s, ".fichas", "display: grid; grid-template-columns: 1fr 1fr; gap: 0.4cm;"),
    "pares_flex": lambda s: _css(_pares(s, '<div class="linha">', "</div>"), ".fichas", "")
    .replace("  .ficha {", "  .linha { display: flex; gap: 0.4cm; margin-bottom: 0.4cm; page-break-inside: avoid; }\n  .ficha {", 1),
    "pares_tabela": lambda s: _css(_pares(s, '<table class="linha"><tr>', "</tr></table>",
                                          '<td class="celula">', "</td>"), ".fichas", "")
    .replace("  .ficha {", "  table.linha { width: 100%; border-collapse: separate; border-spacing: 0; "
             "margin-bottom: 0.4cm; page-break-inside: avoid; }\n  td.celula { width: 50%; vertical-align: top; "
             "padding: 0; }\n  .ficha {", 1),
    # diagnósticos (não são candidatos: mudam a aparência)
    "sem_fotos": lambda s: re.sub(r"\{% if ocorrencia\.foto_data_uri %\}.*?\{% endif %\}", "", s, count=1),
    "sem_rodape": lambda s: re.sub(r"@bottom-center \{[^}]*\}", "", s, count=1),
    "sem_bordas": lambda s: s.replace("border: 0.5pt solid #999", "border: none").replace("#D9D9D9", "transparent"),
    "sem_tabela": lambda s: re.sub(r"<table>.*?</table>", "<p>{{ ocorrencia.descricao }}</p>", s, count=1, flags=re.S),
}


def _pares_tabela2(src: str) -> str:
    """Par de fichas como linha de tabela fixa; a ficha vira a própria célula (alturas iguais)."""
    ini = src.index('<div class="ficha">')
    fim = src.index("</table>", ini) + len("</table>")
    fecha = src.index("</div>", fim)
    corpo = src[ini + len('<div class="ficha">'):fim]
    src = src[:ini] + '<td class="ficha">' + corpo + src[fim:fecha] + "</td>" + src[fecha + len("</div>"):]
    src = src.replace(
        FICHA_LOOP_INI,
        '{% for par in sistema.ocorrencias|batch(2) %}<table class="linha"><tr>'
        '{% for ocorrencia in par %}{% if not loop.first %}<td class="vao"></td>{% endif %}', 1)
    i = src.index("{% endfor %}", src.index("{% for par in"))
    fim_par = ('{% endfor %}{% if par|length == 1 %}<td class="vao"></td><td class="ficha-vazia"></td>{% endif %}'
               '<td class="resto"></td></tr></table>{% endfor %}')
    src = src[:i] + fim_par + src[i + len("{% endfor %}"):]
    src = _css(src, ".fichas", "")
    return src.replace("  .ficha {", "  table.linha { width: 100%; table-layout: fixed; border-collapse: separate; "
                       "border-spacing: 0; margin-bottom: 0.4cm; page-break-inside: avoid; }\n"
                       "  td.vao { width: 0.4cm; padding: 0; }\n  td.ficha-vazia { width: 48.0%; padding: 0; }\n"
                       "  td.resto { padding: 0; }\n  .ficha { padding: 0; vertical-align: top; ", 1)


QUEBRA = "\n  .linha + .linha { page-break-before: always; }\n</style>"
VARIANTES["pares_tabela2"] = _pares_tabela2
VARIANTES["pares_tabela2_quebra"] = lambda s: _pares_tabela2(s).replace("\n</style>", QUEBRA, 1)
VARIANTES["pares_flex_quebra"] = lambda s: VARIANTES["pares_flex"](s).replace("\n</style>", QUEBRA, 1)


def _render_variante(nome: str, n: int) -> str:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from app.services.report_generator import ltip_pipeline as p

    src = (p.TEMPLATES_DIR / p.HTML_TEMPLATE_NAME).read_text(encoding="utf-8")
    fetch = nome.endswith("_fetch")
    nome = nome.removesuffix("_fetch")
    src = VARIANTES[nome](src)
    env = Environment(loader=FileSystemLoader(str(p.TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    ctx, fotos = contexto(n)
    c = p.normalizar_contexto(ctx)
    for sistema in c["sistemas"]:
        for oc in sistema["ocorrencias"]:
            b = p._bytes_da_foto(oc, fotos)
            if b is not None and fetch:
                FETCH[p._storage_key_da_foto(oc)] = b
                oc["foto_data_uri"] = "garra-foto:" + p._storage_key_da_foto(oc)
            elif b is not None:
                import base64
                oc["foto_data_uri"] = f"data:{p._mime(b)};base64,{base64.b64encode(b).decode('ascii')}"
    return env.from_string(src).render(**c)


def cmd_variante(nome: str, n: int) -> None:
    SAIDA.mkdir(exist_ok=True)
    t = time.perf_counter()
    html_str = _render_variante(nome, n)
    jinja = time.perf_counter() - t
    r = _fases(html_str, SAIDA / f"var_{nome}_{n}.pdf")
    r["jinja_s"] = round(jinja, 3)
    print(json.dumps({"variante": nome, "n": n, "rss_pico_mb": round(_rss_mb(), 1), **r}))


def cmd_variantes(n: int, nomes: list[str]) -> None:
    for nome in nomes:
        out = subprocess.run([sys.executable, __file__, "variante", nome, str(n)],
                             capture_output=True, text=True)
        linha = out.stdout.strip().splitlines()[-1] if out.returncode == 0 else json.dumps(
            {"variante": nome, "erro": out.stderr.strip().splitlines()[-1:]})
        print(linha, flush=True)
        with (BENCH / "variantes.jsonl").open("a", encoding="utf-8") as f:
            f.write(linha + "\n")


# --- comparação de geometria ------------------------------------------------------


def _geom(caminho: str) -> list[dict]:
    import pdfplumber

    paginas = []
    with pdfplumber.open(caminho) as pdf:
        for pg in pdf.pages:
            imgs = [(round(i["x0"], 1), round(i["top"], 1), round(i["width"], 1), round(i["height"], 1))
                    for i in pg.images]
            palavras = pg.extract_words()
            paginas.append({"imgs": imgs, "n_chars": len(pg.chars),
                            "palavras": [(w["text"], round(w["x0"], 1), round(w["top"], 1)) for w in palavras]})
    return paginas


def cmd_comparar(a: str, b: str) -> None:
    ga, gb = _geom(a), _geom(b)
    res = {"paginas_a": len(ga), "paginas_b": len(gb), "pag_imgs_diferentes": 0, "max_desvio_img_pt": 0.0,
           "pag_texto_diferente": 0, "max_desvio_palavra_pt": 0.0, "exemplos": []}
    for i, (pa, pb) in enumerate(zip(ga, gb)):
        if len(pa["imgs"]) != len(pb["imgs"]):
            res["pag_imgs_diferentes"] += 1
            res["exemplos"].append(f"p{i + 1}: {len(pa['imgs'])} x {len(pb['imgs'])} imagens")
        for x, y in zip(pa["imgs"], pb["imgs"]):
            res["max_desvio_img_pt"] = max(res["max_desvio_img_pt"], *(abs(u - v) for u, v in zip(x, y)))
        ta, tb = [w[0] for w in pa["palavras"]], [w[0] for w in pb["palavras"]]
        if ta != tb:
            res["pag_texto_diferente"] += 1
            if len(res["exemplos"]) < 5:
                res["exemplos"].append(f"p{i + 1}: texto difere ({len(ta)} x {len(tb)} palavras)")
        else:
            for x, y in zip(pa["palavras"], pb["palavras"]):
                res["max_desvio_palavra_pt"] = max(res["max_desvio_palavra_pt"], abs(x[1] - y[1]), abs(x[2] - y[2]))
    res["max_desvio_img_pt"] = round(res["max_desvio_img_pt"], 2)
    res["max_desvio_palavra_pt"] = round(res["max_desvio_palavra_pt"], 2)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("fotos").add_argument("--n", type=int, default=239)
    u = sp.add_parser("uma")
    u.add_argument("n", type=int)
    u.add_argument("rotulo")
    m = sp.add_parser("medir")
    m.add_argument("--reps", type=int, default=3)
    m.add_argument("--n", type=int, default=239)
    m.add_argument("--rotulo", default="atual")
    f = sp.add_parser("fases")
    f.add_argument("--n", type=int, default=239)
    pr = sp.add_parser("perfil")
    pr.add_argument("--n", type=int, default=239)
    pr.add_argument("--top", type=int, default=45)
    pr.add_argument("--variante", default=None)
    v1 = sp.add_parser("variante")
    v1.add_argument("nome")
    v1.add_argument("n", type=int)
    vs = sp.add_parser("variantes")
    vs.add_argument("--n", type=int, default=60)
    vs.add_argument("nomes", nargs="+")
    c = sp.add_parser("comparar")
    c.add_argument("a")
    c.add_argument("b")
    a = ap.parse_args()
    if a.cmd == "fotos":
        cmd_fotos(a.n)
    elif a.cmd == "uma":
        cmd_uma(a.n, a.rotulo)
    elif a.cmd == "medir":
        cmd_medir(a.reps, a.n, a.rotulo)
    elif a.cmd == "fases":
        cmd_fases(a.n)
    elif a.cmd == "perfil":
        cmd_perfil(a.n, a.top, a.variante)
    elif a.cmd == "variante":
        cmd_variante(a.nome, a.n)
    elif a.cmd == "variantes":
        cmd_variantes(a.n, a.nomes)
    else:
        cmd_comparar(a.a, a.b)
```

## Apêndice B — `comparar_fichas.py` e `paginas.py` (fora do Git)

```python
"""Compara a geometria das páginas de fichas entre dois PDFs do LTIP (T20).

A paginação muda (o título "7.x" deixa de ficar sozinho numa página), então as
páginas são casadas pelo primeiro rótulo "Foto nº NN" e pelo título do sistema.
Para cada par compara: caixas das fotos, posição de cada palavra, retângulos
(fundos cinza) e linhas/curvas (bordas), com tolerância de 0,05 pt.
"""
import json
import sys

import pdfplumber


RODAPE_TOP = 780  # pt: A4 tem 842 pt e a margem inferior é 1,91 cm (54 pt)
TOL = 0.15


def _igual(x, y):
    if len(x) != len(y):
        return False
    for u, v in zip(x, y):
        for a, b in zip(u, v):
            if isinstance(a, float) and isinstance(b, float):
                if abs(a - b) > TOL:
                    return False
            elif a != b:
                return False
    return True


def _chave(pg):
    palavras = pg.extract_words()
    for i, w in enumerate(palavras):
        if w["text"] == "Foto" and i + 2 < len(palavras):
            return palavras[i + 2]["text"], palavras
    return None, palavras


def _geom(pg, palavras):
    r = lambda v: round(v, 1)  # noqa: E731
    return {
        "imgs": sorted((r(i["x0"]), r(i["top"]), r(i["width"]), r(i["height"])) for i in pg.images),
        # sem o rodapé (o número da página muda com a nova paginação)
        "palavras": [(w["text"], r(w["x0"]), r(w["top"])) for w in palavras if w["top"] < RODAPE_TOP],
        "rects": sorted((r(x["x0"]), r(x["top"]), r(x["width"]), r(x["height"]), str(x.get("non_stroking_color")))
                        for x in pg.rects),
        "linhas": sorted((r(x["x0"]), r(x["top"]), r(x["x1"]), r(x["bottom"])) for x in pg.lines + pg.curves),
        "edges": len(pg.edges),
    }


def _mapa(caminho):
    m = {}
    with pdfplumber.open(caminho) as pdf:
        n = len(pdf.pages)
        for pg in pdf.pages:
            chave, palavras = _chave(pg)
            if chave and chave not in m:
                m[chave] = _geom(pg, palavras)
    return m, n


def _desloc(a, b):
    """Deslocamento vertical constante entre as fotos (página com título vs sem título)."""
    if a["imgs"] and b["imgs"]:
        return round(b["imgs"][0][1] - a["imgs"][0][1], 1)
    return 0.0


def main(a, b):
    ma, na = _mapa(a)
    mb, nb = _mapa(b)
    comuns = sorted(set(ma) & set(mb), key=int)
    iguais, deslocadas, diferentes = 0, 0, []
    for k in comuns:
        ga, gb = ma[k], mb[k]
        dy = _desloc(ga, gb)
        if dy:
            # move B para o referencial de A e ignora o título do sistema
            gb = {**gb,
                  "imgs": [(x, round(y - dy, 1), w, h) for x, y, w, h in gb["imgs"]],
                  "palavras": [(t, x, round(y - dy, 1)) for t, x, y in gb["palavras"] if y - dy >= 80],
                  "rects": [(x, round(y - dy, 1), w, h, c) for x, y, w, h, c in gb["rects"]],
                  "linhas": [(x0, round(y0 - dy, 1), x1, round(y1 - dy, 1)) for x0, y0, x1, y1 in gb["linhas"]]}
            ga = {**ga, "palavras": [p for p in ga["palavras"] if p[2] >= 80]}
        campos = [c for c in ("imgs", "palavras", "rects", "linhas") if not _igual(ga[c], gb[c])]
        if not campos:
            iguais += 1
            deslocadas += bool(dy)
        else:
            diferentes.append({"ficha": k, "dy": dy, "campos": campos,
                               **{f"{c}_a": ga[c][:3] for c in campos}, **{f"{c}_b": gb[c][:3] for c in campos}})
    print(json.dumps({"paginas_a": na, "paginas_b": nb, "paginas_de_fichas_comparadas": len(comuns),
                      "identicas": iguais, "identicas_com_deslocamento_vertical": deslocadas,
                      "diferentes": len(diferentes), "exemplos": diferentes[:3]}, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:3])
```

```python
"""Lista, por página, quantas fotos há e a posição/tamanho de cada uma (pt)."""
import sys

import pdfplumber

for caminho in sys.argv[1:]:
    with pdfplumber.open(caminho) as pdf:
        linhas = []
        for i, pg in enumerate(pdf.pages, 1):
            imgs = [f"({i_['x0']:.0f},{i_['top']:.0f} {i_['width']:.0f}x{i_['height']:.0f})" for i_ in pg.images]
            fotos = [t for t in pg.extract_words() if t["text"] == "Foto"]
            h2 = [w["text"] for w in pg.extract_words()[:3]]
            linhas.append(f"p{i}: {len(pg.images)} img {' '.join(imgs)} | rotulos={len(fotos)} | {' '.join(h2)}")
        print(f"== {caminho}: {len(pdf.pages)} páginas")
        print("\n".join(linhas))
```

## Apêndice C — `run.ps1` (fora do Git)

```powershell
# run.ps1 - roda um comando no container do bench (imagem de T17, WeasyPrint 70.0),
# com uma copia de 04_backend (app/, templates/, tests/) montada so-leitura em /app.
# $env:BENCH_APP escolhe a copia (padrao: backend = codigo de T20; backend_antes = HEAD).
# Nao usa compose nem toca nos containers garra-* ja no ar.
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Cmd)
$env:Path = "C:\Program Files\Docker\Docker\resources\bin;" + $env:Path
$copia = if ($env:BENCH_APP) { $env:BENCH_APP } else { 'backend' }
$app = Join-Path $PSScriptRoot $copia
$b = 'C:\Users\dynatest\.claude\jobs\681608b9\tmp\bench'
docker run --rm -i --name garra-bench-t20 --memory 2g --memory-swap 2g `
  -v "${app}:/app:ro" -v "${b}:/bench" -w /app garra-bench-t17-backend `
  sh -c ($Cmd -join ' ')
```
