---
title: Desempenho do PDF da Vistoria Residencial — re-medição pós-T28 (T76)
type: gestao
status: concluido
owner: Garra Engenharia
related:
  - 00_docs/backlog-auto/benchmark-pipelines-finais.md
  - 00_docs/backlog-auto/benchmark-pos-t28.md
  - 00_docs/backlog-auto/ltip-desempenho.md
  - 00_docs/backlog-auto/pipelines-url-fetcher.md
  - 00_docs/projeto/riscos.md
  - 00_docs/estudo-do-contexto.md
tags: [desempenho, rnf-06, r-03, vistoria-residencial, weasyprint, pdf]
last_updated: 2026-11-12
---

# Desempenho do PDF da Vistoria Residencial (T76)

> Tarefa T76 · Data: 2026-11-12 · Branch: `worktree-backlog-T76` · Papel: backend.
> Origem: R-03 (`00_docs/projeto/riscos.md`, linhas 45 e 171). A T17 mediu a Vistoria Residencial a 5 % do limite de RNF-06 ([benchmark-pipelines-finais.md](benchmark-pipelines-finais.md)), e a T28 estendeu o `url_fetcher` a esse pipeline sem medir ([pipelines-url-fetcher.md](pipelines-url-fetcher.md)).

## Resultado: a regra de parada se aplica e o código não foi alterado

| Medida (358 fotos de 1200 px/q72, 200 páginas) | T17 (2026-11-04, 1 execução, antes da T28) | **T76 (mediana de 3, código atual)** | Limite RNF-06 | Margem T76 |
|---|---|---|---|---|
| PDF (`gerar_pdf`, parede) | 49,10 s | **24,16 s** (23,47–24,75) | 60 s | **59,7 %** |
| PDF + DOCX em sequência, só pipeline | 56,7 s | **30,75 s** (24,16 + 6,59) | 60 s | **48,8 %** |
| PDF + DOCX + I/O ilustrativo de 2026-08-05 (11,2 s)¹ | ~68 s | **~41,9 s** | 60 s | **~30 %** |

¹ Mesma soma ilustrativa da T17 (leitura no MinIO 2,0 s + upload/registro 9,2 s, medidos em 2026-08-05 com outro volume). Não foi medida aqui.

A margem do PDF da Vistoria Residencial é de **59,7 %**, acima dos 20 % da regra de parada. Mesmo na conta mais conservadora (job em sequência com o I/O de 2026-08-05), a margem fica em ~30 %. Por isso, **nenhum código foi alterado**: nem pipeline, nem template, nem testes. O arquivo `04_backend/tests/test_vistoria_residencial_desempenho.py` **não foi criado**, porque não há causa corrigida a travar.

O que mudou desde a T17 (49,1 → 24,2 s, −51 %; RSS de pico 420 → 286 MB):

- a T28 trocou os data URIs das fotos por `url_fetcher` (`foto_fetcher.py`), o que elimina o parse de ~41 MB de base64 (`parse` = 0,12 s agora). Na T20, só essa troca reduziu o parse do LTIP de ~2,5 s para 0,28 s e o RSS em ~100 MB;
- a T17 rodou com 0,57 GB livres de 15,7 GB no host e três tarefas em paralelo, e anotou o próprio número como "dentro do ruído de uma execução única". O ganho da T28 (~2–3 s) não explica sozinho os ~25 s de diferença. O restante é atribuído, sem prova, à pressão de memória da sessão da T17. Antes e depois **não** foram medidos na mesma sessão aqui, porque a regra de parada dispensou o "depois".

## Ambiente

| Item | Valor |
|---|---|
| Host | Windows 11 Pro 10.0.26200, Intel Core i7-1355U (12 threads), 15,7 GB de RAM |
| Docker | Docker Desktop 26.1.4 (`C:/Program Files/Docker/Docker/resources/bin`). Containers `garra-*` e Airflow já estavam no ar e **não foram tocados** |
| Imagem | `garra-bench-t17-backend` (a mesma da T17 e da T20): Python 3.12.16, **WeasyPrint 70.0**. Rodada via `docker run --rm --memory 2g` com uma cópia de `04_backend/{app,templates,tests}` montada só-leitura em `/app` (o bind mount direto do worktree falha por causa do "Área" no caminho, como na T20) |
| Código medido | `ef57fd0` (`main` no disparo de T75/T76). O worktree nasceu em `14ead2f`, sem `vistoria_residencial_pipeline.py`, sem este método e sem os Docs citados no briefing. Foi avançado por **fast-forward** até `ef57fd0` antes de qualquer medição (o mesmo que T17 e T20 relatam) |
| Carga concorrente | T75 rodava no mesmo host |

O script `04_backend/app/scripts/benchmark_relatorio_geracao.py`, citado no briefing, **não serve para esta medição**. Ele mede só o RFO (`rfo_pipeline`) e depende de uma inspeção semeada no Postgres/MinIO. Foi usado o método da T17/T20, com dados sintéticos e o pipeline chamado direto (`bench_vr.py`, Apêndice A).

## Dados sintéticos

São os da T17 (Apêndice A de `benchmark-pipelines-finais.md`), reduzidos à Vistoria Residencial:

- fotos `_foto(i)`: 2000×1500 q85 com textura e ruído, reduzidas por `app.services.report_generator.imagem.otimizar_imagem` (1200 px, q72). Com 400 geradas: **88,3 KB** em média, 34,5 MB no total, iguais às da T17 (88 KB);
- contexto: n = 358 fotos (o n que a calibração da T17 deu para 200 páginas), 8 sistemas com 3 constatações e 1 fundamentação, e as 31 chaves de `textos` com 2 parágrafos cada. Confirmado: **200 páginas** em todas as execuções.

Nada foi lido de `01_output-context/`.

## Medição (antes = código atual; não houve "depois")

`bench_vr.py medir --reps 3 --n 358 --rotulo antes`: cada execução roda num subprocesso novo. A medição cobre `gerar_pdf` inteiro (Jinja2 + `HTML().render()` + `write_pdf`) com o WeasyPrint já importado.

| Execução | Parede (s) | `render_html` (s) | `conversao_pdf` (s) | Páginas | RSS pico (MB) | PDF (bytes) |
|---|---|---|---|---|---|---|
| 1 | 24,745 | 0,069 | 24,669 | 200 | 286,2 | 39 427 492 |
| 2 | 23,465 | 0,060 | 23,390 | 200 | 285,7 | 39 427 490 |
| 3 | 24,163 | 0,100 | 24,035 | 200 | 285,7 | 39 427 488 |
| **Mediana** | **24,163** | 0,069 | 24,035 | 200 | 285,7 | 37,6 MB |

Custo por página: **0,121 s** (T17: 0,243 s; LTIP pós-T20: 0,090–0,096 s; RFO: 0,094 s).

DOCX (`gerar_docx`, mesmo contexto, 3 execuções em processos novos): 6,614 / 6,586 / 4,695 s, com **mediana de 6,59 s**, RSS de 78 MB e 31,0 MB de arquivo (T17: 7,64 s).

## Onde está o tempo restante (diagnóstico, sem mudança de código)

Embora a regra de parada dispense a correção, o perfil por fases foi registrado para orientar uma tarefa futura. Cada linha abaixo é **1 execução** de `bench_vr.py fases`/`variantes`, com o mesmo HTML e as mesmas fotos e só o HTML alterado em memória. A coluna "contexto + Jinja2" inclui a leitura das 358 fotos pelo bind mount do Windows e fica fora do pipeline medido.

| Variante | O que muda | contexto + Jinja2 (s) | parse (s) | `render()` (s) | `write_pdf()` (s) | parse + render + write (s) | Páginas | RSS (MB) | PDF (MB) |
|---|---|---|---|---|---|---|---|---|---|
| `base` | template atual | 3,12 | 0,12 | 2,57 | **25,96** | **28,66** | 200 | 252 | 37,6 |
| `sem_logo_cabecalho` | remove o `<img>` do logo SVG do cabeçalho corrido (`position: running(cabecalho)`) | 2,72 | 0,07 | 4,13 | **1,43** | **5,63** | 200 | 151 | 31,2 |
| `logo_cabecalho_png` | o mesmo cabeçalho com `templates/assets/logo-garra.png` (600×543) em vez do SVG | 3,37 | 0,08 | 2,81 | **2,49** | **5,38** | 200 | 155 | 31,3 |
| `sem_object_fit` | remove `object-fit: cover` das figuras | 4,60 | 0,10 | 4,38 | 31,92 | 36,40 | 200 | 250 | 37,6 |
| `sem_fotos` | remove as 358 `<img>` (diagnóstico) | 4,33 | 0,06 | 1,10 | 7,22 | 8,37 | 32 | 142 | 1,1 |

Leitura:

- **O gargalo do PDF não é o layout** (`render()` = 2,6 s, ~9 %). É o `write_pdf()` (26 s, ~90 %).
- **Quase todo o `write_pdf()` vem do logo SVG do cabeçalho corrido.** `logo-garra.svg` tem 76 KB e o desenho vetorizado (2 `<path>` longos, gerados por `bitmap_tracer`). O WeasyPrint 70 redesenha o SVG em cada uma das 200 páginas. Sem ele, o `write_pdf` cai de 25,96 para 1,43 s e o PDF encolhe 6,4 MB. Com o PNG do mesmo logo, cai para 2,49 s.
- `object-fit: cover` e as fotos em si não pesam: `sem_object_fit` fica no ruído, e o custo das fotos no layout é pequeno.
- No `sem_fotos` (32 páginas), o `write_pdf` ainda leva 7,2 s, o que é coerente com o custo por página do logo. Foi só uma execução, então os números servem como ordem de grandeza.
- A causa da T20 (container `flex` único atravessando páginas) **não existe** neste template: as figuras são blocos simples em `.fotos { }`, e `render()` é linear.
- O template da **Vistoria Cautelar** tem o mesmo padrão (`vistoria_cautelar_template.html.j2:50` e `:118`: `running(cabecalho)` com `logo_data_uri`), então provavelmente paga o mesmo custo. Isso não foi medido aqui.

## Recomendação (não aplicada; fica para tarefa própria)

Se for preciso mais folga (I/O real do worker, fotos maiores, mais páginas), a correção de maior efeito medida aqui é **não redesenhar o SVG vetorizado do logo em cada página**. O ganho estimado é ~24 s de 28,7 s (≈ 5×) na Vistoria Residencial. Opções, em ordem de preferência:

1. usar no cabeçalho corrido uma versão raster do logo, com resolução ≥ 300 dpi na largura de 3,86 cm (`logo-garra.png` tem 600 px, ≈ 395 dpi), e manter o SVG só na capa. A mudança vai no gerador `app/scripts/build_vistoria_residencial_templates.py` e no da cautelar (ADR-13/DEC-25), não no `.html.j2`. Antes, confirmar que o PNG é a mesma arte do SVG e comparar a aparência do cabeçalho;
2. ou simplificar o SVG do cabeçalho, com menos nós no traçado (`bitmap_tracer`, `build_brand_assets.py`), mantendo-o vetorial.

Ao fazer isso, travar a causa com um teste determinístico. Por exemplo: o HTML do PDF não referencia `image/svg+xml` dentro de `.cabecalho`, ou o logo do cabeçalho vem de um asset raster.

## Proposta para o fechamento de lote (não aplicada em `riscos.md`/`decisoes.md`)

- **R-03**: registrar que a Vistoria Residencial **atende RNF-06 com folga** pós-T28: PDF de 200 páginas e 358 fotos em 24,2 s (mediana de 3, margem de 59,7 %), PDF + DOCX em 30,8 s e ~42 s com o I/O ilustrativo de 2026-08-05 (~30 %). Com o LTIP pós-T20, nenhum dos tipos medidos fica a menos de 20 % do limite **no pipeline**. Continua pendente a medição do job completo no worker (I/O real) em host dedicado.
- **Proposta DEC-T76-a**: nos templates WeasyPrint, imagem repetida em elemento corrido (`position: running()`, `@top-*`/`@bottom-*`) é raster ou SVG simples, nunca o SVG vetorizado de 76 KB. Motivo: o WeasyPrint 70 redesenha o SVG em cada página, ao custo de ~0,12 s por página (24,5 s em 200 páginas, medido aqui).
- Corrigir a linha 171 de `riscos.md`, que ainda diz "resta a Vistoria Residencial com 5 % de margem".

## Testes

Nenhum arquivo de código ou de teste foi alterado. A única mudança é este Doc. Mesmo assim, os comandos do checklist rodaram em `04_backend`:

```text
$ ruff --version && ruff check . --output-format concise
ruff 0.15.1
All checks passed!
```

`pytest` (venv `04_backend/.venv` do checkout principal, `POSTGRES_DB=garra_engenharia_test` em `localhost:5433` (PostgreSQL de `05_infra` no ar), depois de `alembic upgrade head`, que aplicou `b8d4f2a6c1e7` e `c6f2a8d4e1b9` no banco de teste):

```text
$ python -m pytest -q -p no:cacheprovider
ERROR tests/test_rfo_contexto.py - OSError: cannot load library 'libpango-1.0...
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 warning, 1 error in 31.30s
```

`tests/test_rfo_contexto.py` importa o WeasyPrint na coleta, e o host Windows não tem Pango (B2 de `benchmark-pos-t28.md`). Isso vem do ambiente e não desta tarefa. Rodada sem esse módulo:

```text
$ POSTGRES_DB=garra_engenharia_test python -m pytest -q -p no:cacheprovider --ignore=tests/test_rfo_contexto.py
(sem saída: execução interrompida)
```

**A suíte não terminou.** Depois de mais de 10 minutos, o Claude Code encerrou o processo porque o host estava com pouca memória (T75 rodava em paralelo no mesmo host). Pela regra da sessão, ele não foi reiniciado. **Não há contagem de passed/failed** desta rodada. Como nenhum código mudou, o estado da suíte é o mesmo de `ef57fd0`. Para conferir num host livre: `POSTGRES_DB=garra_engenharia_test python -m pytest -q` em `04_backend`, num ambiente com Pango (container) ou com `--ignore=tests/test_rfo_contexto.py` no Windows.

O `.env` usado (cópia do `04_backend/.env` do checkout principal, com as credenciais do Postgres local) foi copiado para o worktree só durante a rodada e apagado em seguida. Ele está no `.gitignore` e não foi commitado.

## Como reproduzir

```bash
# Diretório do bench: $CLAUDE_JOB_DIR/tmp/bench (fora do Git) com bench_vr.py e run.sh (Apêndices A e B)
# e uma cópia de 04_backend/{app,templates,tests,pytest.ini,conftest.py} em <bench>/backend_antes.
BENCH_APP=backend_antes bash run.sh "python /bench/bench_vr.py fotos --n 400"
BENCH_APP=backend_antes bash run.sh "python /bench/bench_vr.py medir --reps 3 --n 358 --rotulo antes"
BENCH_APP=backend_antes bash run.sh "python /bench/bench_vr.py fases --n 358"
BENCH_APP=backend_antes bash run.sh "python /bench/bench_vr.py variantes --n 358 sem_logo_cabecalho logo_cabecalho_png sem_object_fit sem_fotos"
```

O DOCX foi medido com um `python -c` que chama `bench_vr.contexto(358)` e `vistoria_residencial_pipeline.gerar_docx` três vezes, cada uma num processo novo.

## Apêndice A — `bench_vr.py` (fora do Git)

```python
"""Benchmark/perfil do PDF da Vistoria Residencial (T76, R-03).

Mesmo gerador de fotos e mesmo contexto da T17 (benchmark-pipelines-finais.md,
Apêndice A), reduzidos à Vistoria Residencial. Roda no container do bench
(WeasyPrint 70) com o código em /app e este script + fotos em /bench.

    python /bench/bench_vr.py fotos --n 400
    python /bench/bench_vr.py medir --reps 3 --n 358 --rotulo antes
    python /bench/bench_vr.py fases --n 358
    python /bench/bench_vr.py perfil --n 358 --top 40
    python /bench/bench_vr.py variantes --n 358 base sem_logo_cabecalho ...
"""
from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
import random
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app")
BENCH = Path("/bench")
FOTOS = BENCH / "fotos"
SAIDA = Path("/tmp/saida")
LOREM = (
    "Constatou-se, durante a vistoria, a presença de fissuras de pequena abertura no revestimento "
    "argamassado, com indícios de infiltração por capilaridade junto ao rodapé e manchas de umidade. "
    "Recomenda-se o acompanhamento da evolução e a correção conforme a NBR 13749 e a NBR 16747."
)


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _foto(indice: int) -> bytes:
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
    from app.services.report_generator.imagem import otimizar_imagem

    FOTOS.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        alvo = FOTOS / f"{i:04d}.jpg"
        if not alvo.exists():
            alvo.write_bytes(otimizar_imagem(_foto(i)))  # 1200 px / q72, cenário "otimizado" da T17
    tamanhos = [p.stat().st_size for p in FOTOS.glob("*.jpg")]
    print(json.dumps({"n": len(tamanhos), "media_kb": round(statistics.mean(tamanhos) / 1024, 1),
                      "total_mb": round(sum(tamanhos) / 2**20, 1)}))


def contexto(n: int) -> tuple[dict, dict[str, bytes]]:
    from app.services.report_generator import vistoria_residencial_pipeline as p

    sistemas = [f"Sistema {i + 1}" for i in range(8)]
    keys = [f"{i:04d}.jpg" for i in range(n)]
    ctx = {
        "imovel": {"unidade": "Ap. 101"}, "edificacao": {"nome": "Residencial Sintético"},
        "fiscal": {"nome": "Eng. Sintético", "crea": "0/D-XX", "email": "x@example.com",
                   "telefone": "(00) 0000-0000", "qualificacoes": ["Engenheiro Civil"]},
        "data_emissao": "2026-11-04", "local_emissao": "Goiânia",
        "textos": {c: [LOREM] * 2 for c in p.TEXTOS_CHAVES},
        "fotos": [{"legenda": f"Foto sintética {i + 1}", "storage_key": k} for i, k in enumerate(keys)],
        "sistemas": [{"nome": s, "constatacoes": [LOREM] * 3, "fundamentacao_tecnica": [LOREM]} for s in sistemas],
    }
    return ctx, {k: (FOTOS / k).read_bytes() for k in keys}


def cmd_uma(n: int, rotulo: str) -> None:
    from app.services.report_generator import vistoria_residencial_pipeline as p
    import weasyprint  # noqa: F401  (worker aquecido)

    ctx, fotos = contexto(n)
    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / f"vr_{rotulo}_{n}.pdf"
    rss_antes = _rss_mb()
    t0 = time.perf_counter()
    m = p.gerar_pdf(ctx, fotos, destino)
    parede = time.perf_counter() - t0
    if (BENCH / "pdfs").is_dir():
        (BENCH / "pdfs" / destino.name).write_bytes(destino.read_bytes())
    print(json.dumps({"rotulo": rotulo, "n": n, "parede_s": round(parede, 3), "rss_antes_mb": round(rss_antes, 1),
                      "rss_pico_mb": round(_rss_mb(), 1),
                      **{c: (round(v, 3) if isinstance(v, float) else v) for c, v in m.items()}}))


def cmd_medir(reps: int, n: int, rotulo: str) -> None:
    rs = []
    with (BENCH / "bruto.jsonl").open("a", encoding="utf-8") as bruto:
        for rep in range(1, reps + 1):
            out = subprocess.run([sys.executable, __file__, "uma", str(n), rotulo],
                                 capture_output=True, text=True, check=True)
            r = {"rep": rep, **json.loads(out.stdout.strip().splitlines()[-1])}
            bruto.write(json.dumps(r) + "\n")
            print(json.dumps(r), flush=True)
            rs.append(r)
    t = [r["parede_s"] for r in rs]
    print(json.dumps({"rotulo": rotulo, "n": n, "mediana_s": statistics.median(t), "min": min(t), "max": max(t),
                      "paginas": rs[0]["n_paginas"], "rss_mediano": statistics.median(r["rss_pico_mb"] for r in rs)}))


def _html(n: int, variante: str = "base") -> tuple[str, object]:
    from app.services.report_generator import vistoria_residencial_pipeline as p
    from app.services.report_generator.foto_fetcher import RegistroDeFotos, criar_url_fetcher

    ctx, fotos = contexto(n)
    registro = RegistroDeFotos()
    fetcher = criar_url_fetcher(registro)
    html = p._renderizar(ctx, fotos, registro)
    return VARIANTES[variante](html), fetcher


def _sem(html: str, trecho: str, novo: str = "") -> str:
    assert trecho in html, trecho[:60]
    return html.replace(trecho, novo)


def _logo_cabecalho_png(html: str) -> str:
    import base64
    png = base64.b64encode(Path("/app/templates/assets/logo-garra.png").read_bytes()).decode()
    ini = html.index('<div class="cabecalho"><img src="') + len('<div class="cabecalho"><img src="')
    fim = html.index('"', ini)
    return html[:ini] + "data:image/png;base64," + png + html[fim:]


VARIANTES = {
    "base": lambda h: h,
    "sem_logo_cabecalho": lambda h: h.replace(h[h.index('<div class="cabecalho">'):h.index('</div>', h.index('<div class="cabecalho">'))], '<div class="cabecalho">'),
    "logo_cabecalho_png": _logo_cabecalho_png,
    "sem_cabecalho": lambda h: _sem(h, "@top-right { content: element(cabecalho); vertical-align: top; }"),
    "sem_rodape": lambda h: _sem(h, "@bottom-center { content: element(rodape); vertical-align: top; }"),
    "sem_avoid": lambda h: _sem(h, "page-break-inside: avoid;  }", "}"),
    "sem_fotos": lambda h: __import__("re").sub(r'<img src="garra-foto:\d+" alt="Figura \d+">', "", h),
    "sem_object_fit": lambda h: _sem(h, "height: 9.0cm; object-fit: cover; }", "height: 9.0cm; }"),
}


def cmd_fases(n: int, variante: str) -> None:
    from weasyprint import HTML

    t0 = time.perf_counter()
    html, fetcher = _html(n, variante)
    t1 = time.perf_counter()
    doc = HTML(string=html, base_url="/app/templates", url_fetcher=fetcher)
    t2 = time.perf_counter()
    rend = doc.render()
    t3 = time.perf_counter()
    SAIDA.mkdir(exist_ok=True)
    rend.write_pdf(str(SAIDA / f"fases_{variante}.pdf"))
    t4 = time.perf_counter()
    print(json.dumps({"variante": variante, "n": n, "jinja": round(t1 - t0, 2), "parse": round(t2 - t1, 2),
                      "render": round(t3 - t2, 2), "write_pdf": round(t4 - t3, 2), "total": round(t4 - t1, 2),
                      "paginas": len(rend.pages), "rss_pico_mb": round(_rss_mb(), 1),
                      "pdf_mb": round((SAIDA / f"fases_{variante}.pdf").stat().st_size / 2**20, 1)}), flush=True)


def cmd_perfil(n: int, top: int, ordem: str) -> None:
    from weasyprint import HTML

    html, fetcher = _html(n)
    pr = cProfile.Profile()
    pr.enable()
    rend = HTML(string=html, base_url="/app/templates", url_fetcher=fetcher).render()
    SAIDA.mkdir(exist_ok=True)
    rend.write_pdf(str(SAIDA / "perfil.pdf"))
    pr.disable()
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats(ordem).print_stats(top)
    print(s.getvalue())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("fotos").add_argument("--n", type=int, default=400)
    u = sp.add_parser("uma")
    u.add_argument("n", type=int)
    u.add_argument("rotulo")
    m = sp.add_parser("medir")
    m.add_argument("--reps", type=int, default=3)
    m.add_argument("--n", type=int, default=358)
    m.add_argument("--rotulo", default="x")
    f = sp.add_parser("fases")
    f.add_argument("--n", type=int, default=358)
    f.add_argument("--variante", default="base")
    pf = sp.add_parser("perfil")
    pf.add_argument("--n", type=int, default=358)
    pf.add_argument("--top", type=int, default=40)
    pf.add_argument("--ordem", default="cumulative")
    v = sp.add_parser("variantes")
    v.add_argument("--n", type=int, default=358)
    v.add_argument("nomes", nargs="+")
    a = ap.parse_args()
    if a.cmd == "fotos":
        cmd_fotos(a.n)
    elif a.cmd == "uma":
        cmd_uma(a.n, a.rotulo)
    elif a.cmd == "medir":
        cmd_medir(a.reps, a.n, a.rotulo)
    elif a.cmd == "fases":
        cmd_fases(a.n, a.variante)
    elif a.cmd == "perfil":
        cmd_perfil(a.n, a.top, a.ordem)
    else:
        for nome in a.nomes:  # cada variante num subprocesso novo
            subprocess.run([sys.executable, __file__, "fases", "--n", str(a.n), "--variante", nome], check=True)
```

## Apêndice B — `run.sh` (fora do Git)

```bash
#!/usr/bin/env bash
# run.sh - roda um comando no container do bench (imagem garra-bench-t17-backend, WeasyPrint 70.0),
# com uma copia de 04_backend montada so-leitura em /app. BENCH_APP escolhe a copia
# (backend_antes = HEAD de main; backend = codigo da T76). Nao toca nos containers garra-*.
D="/c/Program Files/Docker/Docker/resources/bin/docker.exe"
B="C:\\Users\\dynatest\\.claude\\jobs\\20df588f\\tmp\\bench"
APP="${BENCH_APP:-backend}"
MSYS_NO_PATHCONV=1 "$D" run --rm -i --name "garra-bench-t76-$$" --memory 2g --memory-swap 2g \
  -v "${B}\\${APP}:/app:ro" -v "${B}:/bench" -w /app garra-bench-t17-backend sh -c "$*"
```
