---
title: Logo raster no cabeçalho corrido das Vistorias Cautelar e Residencial (T92)
type: gestao
status: concluido
owner: Garra Engenharia
related:
  - 00_docs/backlog-auto/vistoria-residencial-desempenho.md
  - 00_docs/projeto/decisoes.md
  - 00_docs/arquitetura.md
tags: [desempenho, rnf-06, r-03, dec-54, vistoria-cautelar, vistoria-residencial, weasyprint, pdf]
last_updated: 2026-11-18
---

# Logo raster no cabeçalho corrido das Vistorias (T92)

> Tarefa T92 · Data: 2026-11-18 · Branch: `worktree-backlog-T92` · Papel: Engenheiro Backend.
> Origem: DEC-54 (proposta da T76, [vistoria-residencial-desempenho.md](vistoria-residencial-desempenho.md)). O WeasyPrint 70 redesenha o logo SVG vetorizado (76 KB) em cada página do cabeçalho corrido (`position: running(cabecalho)`).

## Resultado

| PDF (358 fotos 1200 px/q72, WeasyPrint 70) | Páginas | Antes (mediana de 3) | Depois (mediana de 3) | Ganho | PDF | RSS de pico |
|---|---|---|---|---|---|---|
| Vistoria Residencial, rodada 1 | 200 | 43,74 s | **6,01 s** | 7,3× (−37,7 s) | 37,6 → 31,3 MB | 250 → 156 MB |
| Vistoria Residencial, rodada 2 (controle) | 200 | 30,70 s | **7,64 s** | 4,0× (−23,1 s) | 37,6 → 31,3 MB | 250 → 155 MB |
| Vistoria Cautelar (contexto sintético equivalente) | 213 | 44,83 s | **6,42 s** | 7,0× (−38,4 s) | 38,1 → 31,4 MB | 264 → 168 MB |

- Mesmo número de páginas antes e depois em todas as execuções (200 e 213).
- Medida: parede de `gerar_pdf` (Jinja2 + `HTML().render()` + `write_pdf()`), cada execução num processo novo. O `write_pdf()` isolado não foi separado aqui. Na T76, `render()` levava ~2,6 s e não depende do logo, então quase todo o ganho está no `write_pdf()`.
- As 6 execuções da Residencial juntas dão mediana de **34,79 s antes** e **6,63 s depois** (5,2×).
- Os números absolutos do "antes" ficaram acima dos 24,2 s da T76 por causa da carga do host (ver [Ambiente](#ambiente)). Por isso houve uma segunda rodada, com antes e depois alternados. A razão ficou entre 4× e 7×, coerente com a T76 (o PNG levou o `write_pdf` de 25,96 s para 2,49 s).
- A Cautelar tinha o mesmo custo e nunca tinha sido medida: 44,8 s → 6,4 s.

## O que mudou

### 1. Onde o logo era emitido

Os dois geradores escreviam o mesmo placeholder no cabeçalho corrido e na capa. O pipeline (`vistoria_*_pipeline._logo_data_uri()`) preenche esse placeholder com `data:image/svg+xml;base64,…` de `templates/assets/logo-garra.svg`:

```text
$ grep -n 'class="cabecalho"' templates/vistoria_*/vistoria_*_template.html.j2      # antes
vistoria_cautelar_template.html.j2:118:   <div class="cabecalho">{% if logo_data_uri %}<img src="{{ logo_data_uri }}" ...
vistoria_residencial_template.html.j2:113:<div class="cabecalho">{% if logo_data_uri %}<img src="{{ logo_data_uri }}" ...
```

O CSS dos dois templates faz `.cabecalho { position: running(cabecalho) }` e `@top-right { content: element(cabecalho) }`. O rodapé (`.rodape`, `running(rodape)`) só tem texto e não tinha logo.

### 2. Geradores (ADR-13/DEC-25)

- `04_backend/app/scripts/build_vistoria_cautelar_templates.py`
- `04_backend/app/scripts/build_vistoria_residencial_templates.py`

Cada gerador ganhou `_logo_cabecalho_data_uri()`. A função lê `templates/assets/logo-garra.png` (o mesmo PNG que o DOCX já usa, produzido por `build_brand_assets`) e o embute no template como `data:image/png;base64,…`. Se o PNG faltar, a função levanta `FileNotFoundError` com a instrução para gerá-lo. O `<img>` do cabeçalho continua condicionado a `{% if logo_data_uri %}`: o contexto ainda liga ou desliga o logo, mas o SVG não entra mais no elemento corrido. A capa não mudou e segue com `src="{{ logo_data_uri }}"`, que é o SVG.

O PNG vai embutido no template, e não referenciado por caminho, porque o `url_fetcher` dos pipelines (`foto_fetcher.criar_url_fetcher`, DEC-41) só resolve `data:` e as fotos registradas. Um `src="assets/logo-garra.png"` relativo ao `base_url` cairia no `RegistroDeFotos` e falharia. A alternativa seria uma variável nova de contexto (`logo_cabecalho_data_uri`), mas ela exigiria mexer nos pipelines, que estão fora do escopo desta tarefa. O custo é ~67 KB de base64 numa linha de cada `.html.j2`.

Resolução: o PNG tem 600 × 543 px. Na largura do cabeçalho (109,4 pt = 3,86 cm), isso dá **395 dpi** (mínimo exigido: 300).

### 3. Regeneração

```text
$ cd 04_backend
$ python -m app.scripts.build_vistoria_cautelar_templates
gerados: vistoria_cautelar_template.html.j2, vistoria_cautelar_template.docx
$ python -m app.scripts.build_vistoria_residencial_templates
gerados: vistoria_residencial_template.html.j2, vistoria_residencial_template.docx
$ git status --short
 M app/scripts/build_vistoria_cautelar_templates.py
 M app/scripts/build_vistoria_residencial_templates.py
 M templates/vistoria_cautelar/vistoria_cautelar_template.html.j2
 M templates/vistoria_residencial/vistoria_residencial_template.docx      (ver achado A1)
 M templates/vistoria_residencial/vistoria_residencial_template.html.j2
```

- Cada `.html.j2` mudou só na linha do `<div class="cabecalho">` (`git diff --stat`: 1 linha cada).
- `layout.json` da Cautelar e da Residencial: sem mudança (sem `--original`, o gerador só lê o arquivo).
- DOCX da Cautelar: idêntico byte a byte (o gerador normaliza o ZIP).
- DOCX da Residencial: os 21 membros do ZIP têm **conteúdo idêntico** ao versionado. Só mudou o carimbo de data/hora dos membros (`2026-11-04 13:35:20` → hora da execução). Como o conteúdo é o mesmo, o arquivo versionado foi restaurado (`git restore`) e não entra no commit. Ver achado A1.

### 4. Layout visual inalterado

Caixa do logo na margem `@top-right` da página 3, medida na árvore de layout do WeasyPrint 70 (contexto de 4 fotos, `caixa_logo.py`). Valores em px CSS (1 px = 0,75 pt):

| Template | Antes (SVG) x / y / largura / altura | Depois (PNG) x / y / largura / altura |
|---|---|---|
| Residencial | 572,60 / 17,01 / 145,89 / 132,09 | 572,60 / 17,01 / 145,89 / 132,03 |
| Cautelar | 571,11 / 17,07 / 145,87 / 132,07 | 571,11 / 17,07 / 145,87 / 132,01 |

Posição e largura são iguais. A altura difere 0,06 px (0,045 pt), que é o arredondamento de 1 px na altura do PNG.

> Observação fora do escopo: o `layout.json` mede o logo do cabeçalho do original com 109,4 × 52,3 pt (proporção 2,09:1). A marca atual (`logo-garra.svg`/`.png`, recorte 814 × 737) tem proporção 1,10:1 e por isso ocupa ~99 pt de altura no cabeçalho. Isso já acontecia com o SVG e não mudou aqui.

## Teste novo: `04_backend/tests/test_vistoria_cabecalho_raster.py`

O teste é determinístico: só lê arquivos versionados e não usa WeasyPrint nem banco. Ele roda nos dois `.html.j2` versionados e também na saída atual de `gerar_html(layout)` de cada gerador. São 17 casos:

- `test_cabecalho_e_rodape_sem_svg`: extrai as regras CSS do `<style>` cujo seletor cita `cabecalho`/`rodape`, ou que fazem `element(cabecalho|rodape)`, e o `<div class="cabecalho|rodape">` do corpo com os `<div>` aninhados. Nenhum desses trechos pode conter `image/svg+xml` nem `.svg`.
- `test_cabecalho_renderizado_ignora_o_svg_do_pipeline`: renderiza o trecho do cabeçalho com Jinja2 passando um `logo_data_uri` SVG, como o pipeline faz. A saída não tem `image/svg+xml` e tem `<img src="data:image/png;base64,`. Sem `logo_data_uri`, o cabeçalho sai sem `<img>`.
- `test_capa_continua_com_o_logo_do_contexto`: o SVG continua permitido e em uso na capa (`src="{{ logo_data_uri }}"`).
- `test_png_embutido_e_o_asset_da_marca`: o base64 do cabeçalho decodifica byte a byte para `templates/assets/logo-garra.png`, com ≥ 300 dpi na `largura_pt` do cabeçalho em `layout.json`.
- `test_largura_do_logo_no_cabecalho_inalterada`: a `width` de `.cabecalho img` no CSS é a `largura_pt` do layout, com tolerância de 0,3 pt (a Residencial escreve em cm com 2 casas).
- `test_png_tem_a_proporcao_do_svg`: a proporção do PNG (cabeçalho IHDR) e a do `viewBox` do SVG diferem no máximo **0,5 %** (`TOLERANCIA_PROPORCAO`). O valor medido é 0,045 %: 600/543 = 1,1050 contra 814/737 = 1,1045. O teste também confere que `marca.json.recorte_px` é o `viewBox`.

Prova de que o teste pega a regressão: aplicado aos templates anteriores (cópia `backend_antes`), o cabeçalho renderizado com o `logo_data_uri` do pipeline contém `image/svg+xml` nos dois tipos. Com isso, `test_cabecalho_renderizado_ignora_o_svg_do_pipeline` e `test_png_embutido_e_o_asset_da_marca` falhariam.

## Achados (somente leitura, nada editado)

| # | Onde | Achado |
|---|---|---|
| A1 | `build_vistoria_residencial_templates.py` | O DOCX gerado não é byte-idêntico entre execuções: o ZIP sai com a hora atual em cada membro. O gerador da Cautelar normaliza o ZIP (`_normalizar_zip`, `DATA_FIXA`), mas o da Residencial não. Cada regeneração suja o `git status` sem mudança real. Sugestão: aplicar a mesma normalização. Fica fora desta tarefa porque não é desempenho de PDF. |
| A2 | **RFIP** (`templates/rfip/rfip_template.html.j2:17,31,49`; `build_rfip_templates.py:387`) | **Mesmo padrão das vistorias**: `.logo { position: running(logo) }` + `@top-right { content: element(logo) }` com `src="{{ logo_data_uri }}"`. O `rfip_pipeline` (linha 102) preenche esse valor com `ltip_pipeline._logo_data_uri()`, que é o SVG. O custo deve ser o mesmo (~0,12 s por página, T76). Candidato direto à mesma correção no `build_rfip_templates.py`. |
| A3 | **RFO** (`templates/rfo/rfo_template.html.j2:60-69,108`) | O RFO não usa elemento corrido. O SVG (`rfo_pipeline._logo_data_uri()`, `image/svg+xml`) entra pela macro `marca()`, chamada uma vez na capa e **uma vez por visita**. O custo cresce com o número de visitas, não de páginas. Não foi medido. |
| A4 | **LTIP** (`templates/ltip/ltip_template.html.j2:81`) | O SVG aparece só na capa (`.capa .logo`). Não há cabeçalho corrido com logo. Sem o problema. |

## Proposta para o fechamento de lote

- **DEC-54**: registrar como aplicada às Vistorias Cautelar e Residencial (T92). Regra: em elemento corrido (`position: running()`, `@top-*`/`@bottom-*`), o logo é o PNG de `templates/assets/` embutido pelo gerador; o SVG fica restrito à capa.
- **Backlog**: tarefa irmã para o RFIP (achado A2), com a mesma mudança em `build_rfip_templates.py` e o mesmo teste. Opcionalmente, medir o RFO com muitas visitas (achado A3) e normalizar o ZIP do DOCX da Residencial (achado A1).
- **R-03**: com os números acima, a Vistoria Residencial de 200 páginas cai de ~24–44 s para ~6–8 s de PDF neste host.

## Ambiente

| Item | Valor |
|---|---|
| Host | Windows 11 Pro, 15,7 GB de RAM, **1,3 GB livres** no início (outras tarefas do lote rodando em paralelo). Isso explica a variância do "antes" (34–65 s) |
| Docker | `C:/Program Files/Docker/Docker/resources/bin`; containers `garra-*` e Airflow já no ar e **não tocados** |
| Imagem do bench | `garra-bench-t17-backend` (a mesma da T17/T20/T76): Python 3.12.16, **WeasyPrint 70.0**, `docker run --rm --memory 2g`, com a cópia de `04_backend/{app,templates,tests,pytest.ini}` montada só-leitura em `/app` |
| Antes | `39fcfb3` (`main` no disparo, após `git merge --no-edit main`), copiado para `<bench>/backend_antes` antes de qualquer edição |
| Depois | código desta tarefa, copiado para `<bench>/backend_depois` |
| Dados | 358 fotos sintéticas (gerador da T17/T76, `otimizar_imagem` 1200 px/q72, média de 88,3 KB). Residencial: o mesmo contexto da T76 (`bench_vr.py`). Cautelar: as mesmas 358 fotos como `figuras`, 8 sistemas, 2 parágrafos em cada uma das 31 chaves `conteudo.get('…')` do template, `parecer_tecnico` e 20 linhas em cada tabela |
| Script | `04_backend/app/scripts/benchmark_relatorio_geracao.py` **não serve** (mede só o RFO e exige inspeção semeada no Postgres/MinIO), como a T76 já tinha registrado. Foi usado `bench_vist.py`, derivado do `bench_vr.py` da T76 com a Cautelar acrescentada. Fica fora do Git, em `$CLAUDE_JOB_DIR/tmp/bench` |

### Saída bruta (`bench_vist.py medir`)

```text
# rodada 1: antes (VR, VC) -> depois (VR, VC)
{"rep": 1, "tipo": "vr", "rotulo": "antes", "parede_s": 65.387, "conversao_pdf": 65.208, "n_paginas": 200, "tamanho_bytes": 39427492}
{"rep": 2, "tipo": "vr", "rotulo": "antes", "parede_s": 43.737, "conversao_pdf": 43.426, "n_paginas": 200, "tamanho_bytes": 39427487}
{"rep": 3, "tipo": "vr", "rotulo": "antes", "parede_s": 34.409, "conversao_pdf": 34.247, "n_paginas": 200, "tamanho_bytes": 39427492}
{"tipo": "vr", "rotulo": "antes", "mediana_parede_s": 43.737, "mediana_conversao_pdf_s": 43.426, "paginas": [200, 200, 200], "pdf_mb": 37.6, "rss_mediano": 249.8}
{"rep": 1, "tipo": "vc", "rotulo": "antes", "parede_s": 45.603, "conversao_pdf": 45.491, "n_paginas": 213, "tamanho_bytes": 39905937}
{"rep": 2, "tipo": "vc", "rotulo": "antes", "parede_s": 40.887, "conversao_pdf": 40.724, "n_paginas": 213, "tamanho_bytes": 39905936}
{"rep": 3, "tipo": "vc", "rotulo": "antes", "parede_s": 44.832, "conversao_pdf": 44.719, "n_paginas": 213, "tamanho_bytes": 39905933}
{"tipo": "vc", "rotulo": "antes", "mediana_parede_s": 44.832, "mediana_conversao_pdf_s": 44.719, "paginas": [213, 213, 213], "pdf_mb": 38.1, "rss_mediano": 264.3}
{"rep": 1, "tipo": "vr", "rotulo": "depois", "parede_s": 6.718, "conversao_pdf": 6.588, "n_paginas": 200, "tamanho_bytes": 32867584}
{"rep": 2, "tipo": "vr", "rotulo": "depois", "parede_s": 5.166, "conversao_pdf": 5.021, "n_paginas": 200, "tamanho_bytes": 32867584}
{"rep": 3, "tipo": "vr", "rotulo": "depois", "parede_s": 6.005, "conversao_pdf": 5.864, "n_paginas": 200, "tamanho_bytes": 32867584}
{"tipo": "vr", "rotulo": "depois", "mediana_parede_s": 6.005, "mediana_conversao_pdf_s": 5.864, "paginas": [200, 200, 200], "pdf_mb": 31.3, "rss_mediano": 155.8}
{"rep": 1, "tipo": "vc", "rotulo": "depois", "parede_s": 7.251, "conversao_pdf": 7.057, "n_paginas": 213, "tamanho_bytes": 32902397}
{"rep": 2, "tipo": "vc", "rotulo": "depois", "parede_s": 6.416, "conversao_pdf": 6.189, "n_paginas": 213, "tamanho_bytes": 32902391}
{"rep": 3, "tipo": "vc", "rotulo": "depois", "parede_s": 5.493, "conversao_pdf": 5.387, "n_paginas": 213, "tamanho_bytes": 32902388}
{"tipo": "vc", "rotulo": "depois", "mediana_parede_s": 6.416, "mediana_conversao_pdf_s": 6.189, "paginas": [213, 213, 213], "pdf_mb": 31.4, "rss_mediano": 168.0}
# rodada 2 (controle de deriva): antes (VR) -> depois (VR)
{"rep": 1, "tipo": "vr", "rotulo": "antes2", "parede_s": 27.958, "conversao_pdf": 27.87, "n_paginas": 200}
{"rep": 2, "tipo": "vr", "rotulo": "antes2", "parede_s": 30.701, "conversao_pdf": 30.609, "n_paginas": 200}
{"rep": 3, "tipo": "vr", "rotulo": "antes2", "parede_s": 35.172, "conversao_pdf": 35.058, "n_paginas": 200}
{"tipo": "vr", "rotulo": "antes2", "mediana_parede_s": 30.701, "mediana_conversao_pdf_s": 30.609, "paginas": [200, 200, 200], "pdf_mb": 37.6, "rss_mediano": 250.1}
{"rep": 1, "tipo": "vr", "rotulo": "depois2", "parede_s": 8.437, "conversao_pdf": 8.184, "n_paginas": 200}
{"rep": 2, "tipo": "vr", "rotulo": "depois2", "parede_s": 7.64, "conversao_pdf": 7.473, "n_paginas": 200}
{"rep": 3, "tipo": "vr", "rotulo": "depois2", "parede_s": 6.544, "conversao_pdf": 6.407, "n_paginas": 200}
{"tipo": "vr", "rotulo": "depois2", "mediana_parede_s": 7.64, "mediana_conversao_pdf_s": 7.473, "paginas": [200, 200, 200], "pdf_mb": 31.3, "rss_mediano": 155.1}
```

### Como reproduzir

```bash
# <bench> = $CLAUDE_JOB_DIR/tmp/bench, com bench_vist.py, run.sh e as cópias backend_antes/backend_depois de 04_backend
BENCH_APP=backend_antes  bash run.sh "python /bench/bench_vist.py fotos --n 358"
BENCH_APP=backend_antes  bash run.sh "python /bench/bench_vist.py medir --tipo vr --reps 3 --n 358 --rotulo antes"
BENCH_APP=backend_antes  bash run.sh "python /bench/bench_vist.py medir --tipo vc --reps 3 --n 358 --rotulo antes"
BENCH_APP=backend_depois bash run.sh "python /bench/bench_vist.py medir --tipo vr --reps 3 --n 358 --rotulo depois"
BENCH_APP=backend_depois bash run.sh "python /bench/bench_vist.py medir --tipo vc --reps 3 --n 358 --rotulo depois"
BENCH_APP=backend_antes  bash run.sh "python /bench/caixa_logo.py"   # idem com backend_depois
```

`run.sh` é o do Apêndice B da T76, com o nome do container `garra-bench-t92-$$`. `bench_vist.py` é o `bench_vr.py` da T76 (Apêndice A) com `contexto_vc()` acrescentado e `uma`/`medir` parametrizados por `--tipo vr|vc`.

## Testes

Banco isolado `garra_engenharia_test` (Postgres de `05_infra`, `localhost:5433`), migrado antes. Venv `04_backend/.venv` do checkout principal, porque o worktree não tem venv próprio. Variáveis carregadas do `04_backend/.env` de dev, com `POSTGRES_DB` sobrescrito.

```text
$ cd 04_backend
$ export POSTGRES_DB=garra_engenharia_test
$ python -m alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.

$ ruff check .
All checks passed!

$ python -m pytest -q -p no:cacheprovider tests/test_vistoria_cabecalho_raster.py      # Windows
17 passed, 1 warning in 1.79s

$ python -m pytest -q -p no:cacheprovider                                               # Windows, suíte inteira
ERROR tests/test_rfo_contexto.py - OSError: cannot load library 'libpango-1.0-0': error 0x7e.
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 warning, 1 error in 26.34s
```

O erro de coleta acima já existia: `test_rfo_contexto.py` importa o WeasyPrint, que não tem Pango no Windows. A T76 registrou o mesmo erro. Para cobrir os testes que dependem do WeasyPrint, os testes de templates e pipelines das duas vistorias, mais o `test_rfo_contexto.py`, rodaram no container do bench (WeasyPrint 70 + Pango), com o código desta tarefa e o mesmo banco de teste via `host.docker.internal:5433`:

```text
$ python -m pytest -q -p no:cacheprovider -rfE tests/test_rfo_contexto.py tests/test_vistoria_cabecalho_raster.py \
    tests/test_vistoria_cautelar_templates.py tests/test_vistoria_cautelar_pipeline.py tests/test_vistoria_cautelar_contexto.py \
    tests/test_vistoria_residencial_templates.py tests/test_vistoria_residencial_pipeline.py \
    tests/test_vistoria_residencial_contexto.py tests/test_legenda_relatorio_vistorias.py
119 passed, 3 warnings in 67.17s (0:01:07)
```

Uma rodada anterior no container, sem acesso ao banco, deu `2 failed, 98 passed, 19 errors`. Todas as falhas e erros eram `Connect call failed ('127.0.0.1', 5432)`, e todos passaram quando o container passou a apontar para o banco de teste.

**A suíte inteira no Windows não terminou.** O comando `python -m pytest -q -p no:cacheprovider --ignore=tests/test_rfo_contexto.py` rodou por mais de 25 minutos, avançando devagar e conectado ao banco de teste, até o Claude Code encerrá-lo porque o host ficou com pouca memória (1,3–1,9 GB livres, com outras tarefas do lote em paralelo). Pela regra da sessão, ele não foi reiniciado e **não há contagem de passed/failed dessa rodada**. Esta tarefa só alterou os dois geradores, os dois `.html.j2` e um teste novo, e os testes que leem esses arquivos estão entre os 119 acima. Para conferir num host livre: `POSTGRES_DB=garra_engenharia_test python -m pytest -q --ignore=tests/test_rfo_contexto.py` em `04_backend` no Windows, ou a suíte inteira no container.
