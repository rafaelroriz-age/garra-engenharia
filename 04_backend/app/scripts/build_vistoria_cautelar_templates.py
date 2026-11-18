"""Deriva os templates da Vistoria Cautelar (HTML/Jinja2 + DOCX) do `layout.json`.

Fatia "Vistoria Cautelar" de ADR-13/DEC-25, irmã de `build_ltip_templates`:

    01_output-context/Laudo Técnico de Vistoria Cautelar de Recebimento - ....pdf
        -> app/scripts/vistoria_cautelar_layout_extractor.extrair_layout()
        -> 04_backend/templates/vistoria_cautelar/layout.json                      (versionado)
        -> 04_backend/templates/vistoria_cautelar/vistoria_cautelar_template.html.j2 (WeasyPrint, ADR-01)
        -> 04_backend/templates/vistoria_cautelar/vistoria_cautelar_template.docx    (docxtpl, ADR-04)

Uso:

    python -m app.scripts.build_vistoria_cautelar_templates \\
        --original "../01_output-context/Laudo Técnico de Vistoria Cautelar de Recebimento - Reforma New York - V01.pdf"

Sem `--original`, reutiliza o `layout.json` versionado (CI e máquinas sem o
arquivo do cliente). A geração é determinística: o mesmo `layout.json` produz o
mesmo `.html.j2` e o mesmo `.docx`, byte a byte (o ZIP do DOCX é normalizado).

Contexto esperado pelos dois templates (o pipeline de renderização é tarefa à
parte, como `ltip_pipeline.py`):

- `responsavel`: `nome`, `titulo_profissional`, `crea`, `email`, `telefone`, `qualificacoes` (lista)
- `obra.descricao`, `edificacao.nome`, `data_emissao_mes_ano`, `data_emissao_extenso`, `local_emissao`
- `conteudo`: dict `chave -> [parágrafos]` com as chaves de `layout.estrutura`
- `complementos`: dict `chave -> texto` (ex.: resultado do parecer técnico)
- `sistemas`: lista de `{nome, <rótulo>: [parágrafos]}` (ex.: `constatacoes`, `fundamentacao_tecnica`)
- `figuras`: lista de `{numero, legenda, foto_data_uri (HTML) | imagem (DOCX, InlineImage)}`
- `tabelas`: dict `chave -> [linhas]`, cada linha com as chaves das colunas medidas
- HTML: `logo_data_uri`, `capa_fundo_data_uri`, `assinatura_data_uri` (opcionais).
  `logo_data_uri` (o SVG) só entra na capa; no cabeçalho corrido ele apenas liga o
  logo, que sai do PNG embutido no template (DEC-54, ver `_logo_cabecalho_data_uri`).
- DOCX: `assinatura_imagem` (InlineImage, opcional)
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import sys
import zipfile
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from app.scripts.vistoria_cautelar_layout_extractor import LayoutExtractionError, extrair_layout

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates" / "vistoria_cautelar"
LAYOUT_JSON = TEMPLATES_DIR / "layout.json"
HTML_TEMPLATE = TEMPLATES_DIR / "vistoria_cautelar_template.html.j2"
DOCX_TEMPLATE = TEMPLATES_DIR / "vistoria_cautelar_template.docx"
# Marca com fundo transparente (RN-07/ADR-16), a mesma usada pelo LTIP; o DOCX não aceita SVG.
LOGO_PNG = TEMPLATES_DIR.parent / "assets" / "logo-garra.png"

PT_POR_CM = 72 / 2.54
#: Data fixa gravada no ZIP e nas propriedades do DOCX: garante saída idêntica byte a byte.
DATA_FIXA = datetime(2026, 1, 1, tzinfo=UTC)
#: Largura média do "_" em Calibri 12 (pt): converte a largura medida do traço em caracteres.
LARGURA_SUBLINHADO_PT = 6.0

CABECALHO_GERADO = (
    "ARQUIVO GERADO — não editar à mão. "
    "Produzido por `python -m app.scripts.build_vistoria_cautelar_templates` a partir de "
    "templates/vistoria_cautelar/layout.json (ADR-13/DEC-25)."
)


def _e(texto: str) -> str:
    """Escapa rótulo fixo vindo do layout (placeholders `{{ }}` não têm `<>&`)."""
    return html.escape(texto, quote=False)


def _logo_cabecalho_data_uri() -> str:
    """PNG da marca como data URI, para o logo do cabeçalho corrido (DEC-54).

    O WeasyPrint 70 redesenha o SVG vetorizado (76 KB) em cada página de um
    elemento `running()` (~0,12 s por página, T76). O PNG de `build_brand_assets`
    tem a mesma arte e 600 px de largura (≈ 400 dpi nos 109 pt do cabeçalho).
    Embutido no template porque o `url_fetcher` dos pipelines só resolve `data:`
    e as fotos registradas (DEC-41).
    """
    if not LOGO_PNG.is_file():
        raise FileNotFoundError(f"{LOGO_PNG} não existe: rode `python -m app.scripts.build_brand_assets`.")
    return "data:image/png;base64," + base64.b64encode(LOGO_PNG.read_bytes()).decode("ascii")


def _fonte_do_nivel(layout: dict[str, Any], nivel: int) -> float:
    for titulo in layout.get("titulos", []):
        if titulo["nivel"] == nivel:
            return titulo["fonte_pt"]
    return layout["tipografia"]["titulo_pt"]


def _recuo_do_nivel(layout: dict[str, Any], nivel: int) -> float:
    for titulo in layout.get("titulos", []):
        if titulo["nivel"] == nivel:
            return titulo.get("recuo_cm", 0.0)
    return 0.0


def _tabelas_por_chave(layout: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {tabela["chave"]: tabela for tabela in layout.get("tabelas") or []}


def _legenda_modelo(layout: dict[str, Any]) -> str:
    legenda = layout["relatorio_fotografico"]["legenda"]
    sufixo = f" {legenda['sufixo_fonte']}" if legenda.get("sufixo_fonte") else ""
    return f"{legenda['rotulo']} {{{{ figura.numero }}}} {legenda['separador']} {{{{ figura.legenda }}}}{sufixo}"


def _plano_de_secoes(layout: dict[str, Any]) -> list[dict[str, Any]]:
    """Sequência linear de blocos do corpo — a mesma para HTML e DOCX (RF-06)."""
    blocos: list[dict[str, Any]] = []
    for secao in layout["estrutura"]["secoes"]:
        numero = secao["numero"]
        blocos.append({"tipo": "titulo", "nivel": 1, "numero": numero, "texto": secao["titulo"], "ancora": f"s-{numero}"})
        blocos.append({"tipo": "paragrafos", "chave": secao["chave"]})
        blocos += [{"tipo": "tabela", "chave": chave} for chave in secao.get("tabelas", [])]

        if secao["tipo"] == "relatorio_fotografico":
            blocos.append({"tipo": "figuras"})

        subsecoes = secao["subsecoes"]
        antes = [sub for sub in subsecoes if sub.get("posicao") != "depois_dos_sistemas"]
        depois = [sub for sub in subsecoes if sub.get("posicao") == "depois_dos_sistemas"]
        for sub in antes:
            blocos += _blocos_de_subsecao(sub, sub["numero"])
        if secao["tipo"] == "por_sistema":
            blocos.append({"tipo": "sistemas", "numero": numero, "rotulos": secao["rotulos_por_sistema"]})
            # Subseções fixas depois dos sistemas são renumeradas pela quantidade real de sistemas.
            for ordem, sub in enumerate(depois, start=1):
                blocos += _blocos_de_subsecao(sub, f"{numero}.{{{{ sistemas|length + {ordem} }}}}")
        else:
            for sub in depois:
                blocos += _blocos_de_subsecao(sub, sub["numero"])

        if secao["tipo"] == "encerramento" and layout.get("assinatura"):
            blocos.append({"tipo": "assinatura"})
    return blocos


def _blocos_de_subsecao(sub: dict[str, Any], numero: str) -> list[dict[str, Any]]:
    ancora = "s-" + sub["numero"].replace(".", "-")
    blocos: list[dict[str, Any]] = [
        {
            "tipo": "titulo",
            "nivel": 2,
            "numero": numero,
            "texto": sub["titulo"],
            "ancora": ancora,
            "complemento": sub.get("complemento"),
        },
        {"tipo": "paragrafos", "chave": sub["chave"]},
    ]
    blocos += [{"tipo": "tabela", "chave": chave} for chave in sub.get("tabelas", [])]
    return blocos


# --------------------------------------------------------------------------------------
# HTML (WeasyPrint)
# --------------------------------------------------------------------------------------


def _html_titulo(bloco: dict[str, Any]) -> str:
    texto = _e(bloco["texto"])
    complemento = bloco.get("complemento")
    if complemento:
        chave = complemento["chave"]
        texto += (
            f"{{% if complementos.get('{chave}') %}} {complemento['separador']} "
            f"{{{{ complementos.get('{chave}') }}}}{{% endif %}}"
        )
    return f'  <h{bloco["nivel"]} id="{bloco["ancora"]}">{bloco["numero"]}. {texto}</h{bloco["nivel"]}>'


def _html_tabela(tabela: dict[str, Any]) -> str:
    colunas = tabela["colunas"]
    cols = "".join(f'<col style="width: {coluna["largura_pct"]}%">' for coluna in colunas)
    cabecalho = "".join(f"<th>{_e(coluna['rotulo'])}</th>" for coluna in colunas)
    celulas = "".join(f"<td>{{{{ linha.{coluna['chave']} }}}}</td>" for coluna in colunas)
    return (
        f'  <table class="tabela tabela-{tabela["chave"]}">\n'
        f"    <colgroup>{cols}</colgroup>\n"
        f"    <thead><tr>{cabecalho}</tr></thead>\n"
        f"    <tbody>\n"
        f"      {{% for linha in tabelas.get('{tabela['chave']}', []) %}}<tr>{celulas}</tr>{{% endfor %}}\n"
        f"    </tbody>\n"
        f"  </table>"
    )


def _html_sistemas(bloco: dict[str, Any]) -> str:
    numero = bloco["numero"]
    partes = [
        "  {% for sistema in sistemas %}",
        f'  <h2 id="s-{numero}-{{{{ loop.index }}}}">{numero}.{{{{ loop.index }}}}. {{{{ sistema.nome }}}}</h2>',
    ]
    for ordem, rotulo in enumerate(bloco["rotulos"], start=1):
        partes += [
            f"  <h3>{numero}.{{{{ loop.index }}}}.{ordem}. {_e(rotulo['titulo'])}</h3>",
            f"  {{% for paragrafo in sistema.get('{rotulo['chave']}', []) %}}<p>{{{{ paragrafo }}}}</p>{{% endfor %}}",
        ]
    partes.append("  {% endfor %}")
    return "\n".join(partes)


def _html_assinatura(layout: dict[str, Any]) -> str:
    assinatura = layout["assinatura"]
    linhas = []
    for modelo in assinatura["linhas"]:
        classe = ' class="nome"' if modelo == "{{ responsavel.nome }}" else ""
        linhas.append(f"    <div{classe}>{modelo}</div>")
    linhas.append("    {% for linha in responsavel.qualificacoes %}<div>{{ linha }}</div>{% endfor %}")
    local_data = assinatura.get("local_data")
    rodape = f'    <div class="local-data">{local_data["modelo"]}</div>\n' if local_data else ""
    return (
        '  <div class="assinatura">\n'
        '    {% if assinatura_data_uri %}<img class="rubrica" src="{{ assinatura_data_uri }}" alt="Assinatura">{% endif %}\n'
        '    <div class="traco"></div>\n' + "\n".join(linhas) + "\n" + rodape + "  </div>"
    )


def _html_sumario(layout: dict[str, Any], blocos: list[dict[str, Any]]) -> str:
    itens = []
    for bloco in blocos:
        if bloco["tipo"] == "titulo":
            itens.append(
                f'    <li class="n{bloco["nivel"]}"><a href="#{bloco["ancora"]}">{bloco["numero"]}. {_e(bloco["texto"])}</a></li>'
            )
        elif bloco["tipo"] == "sistemas":
            numero = bloco["numero"]
            itens.append("    {% for sistema in sistemas %}")
            itens.append(
                f'    <li class="n2"><a href="#s-{numero}-{{{{ loop.index }}}}">{numero}.{{{{ loop.index }}}}. {{{{ sistema.nome }}}}</a></li>'
            )
            itens.append("    {% endfor %}")
    titulo = _e((layout.get("sumario") or {}).get("titulo") or "SUMÁRIO")
    return '  <nav class="sumario">\n' f'    <div class="titulo-sumario">{titulo}</div>\n    <ul>\n' + "\n".join(itens) + "\n    </ul>\n  </nav>"


def _html_capa(layout: dict[str, Any]) -> str:
    capa = layout["capa"]
    titulo = capa["titulo"]
    partes = [
        '  <section class="capa">',
        '    {% if capa_fundo_data_uri %}<img class="fundo" src="{{ capa_fundo_data_uri }}" alt="">{% endif %}',
    ]
    if capa.get("logo"):
        logo = capa["logo"]
        partes.append(
            f'    {{% if logo_data_uri %}}<img class="logo" style="left: {logo["x_pt"]}pt; top: {max(logo["topo_pt"], 0)}pt; '
            f'width: {logo["largura_pt"]}pt" src="{{{{ logo_data_uri }}}}" alt="Garra Engenharia">{{% endif %}}'
        )
    partes.append(
        f'    <div class="titulo" style="left: {titulo["x_pt"]}pt; top: {titulo["topo_pt"]}pt">'
        + "<br>".join(_e(linha) for linha in titulo["linhas"])
        + "</div>"
    )
    for indice, elemento in enumerate(capa["elementos"]):
        if elemento.get("faixa"):
            faixa = elemento["faixa"]
            partes.append(
                f'    <div class="faixa" style="left: {faixa["x_pt"]}pt; top: {faixa["topo_pt"]}pt; '
                f'width: {faixa["largura_pt"]}pt; height: {faixa["altura_pt"]}pt"></div>'
            )
        if elemento["alinhamento"] == "right":
            posicao = f"right: {round(layout['pagina']['largura_pt'] - elemento['borda_direita_pt'], 1)}pt; text-align: right"
        else:
            posicao = f"left: {elemento['x_pt']}pt"
        partes.append(
            f'    <div class="elemento elemento-{elemento["papel"]} e{indice}" style="{posicao}; top: {elemento["topo_pt"]}pt">'
            + "<br>".join(elemento["linhas"])
            + "</div>"
        )
    partes.append("  </section>")
    return "\n".join(partes)


def _html_folha_de_rosto(layout: dict[str, Any]) -> str:
    folha = layout.get("folha_de_rosto")
    if not folha:
        return ""
    topo_util = layout["pagina"]["margens_cm"]["superior"] * PT_POR_CM
    partes = ['  <section class="folha-rosto">']
    titulo = folha["titulo"]
    partes.append(
        f'    <div class="titulo" style="top: {round(titulo["topo_pt"] - topo_util, 1)}pt">'
        + "<br>".join(_e(linha) for linha in titulo["linhas"])
        + "</div>"
    )
    for papel in ("objeto", "data"):
        if folha.get(papel):
            item = folha[papel]
            partes.append(
                f'    <div class="{papel}" style="top: {round(item["topo_pt"] - topo_util, 1)}pt">{item["modelo"]}</div>'
            )
    partes.append("  </section>")
    return "\n".join(partes)


def gerar_html(layout: dict[str, Any]) -> str:
    """Monta o `.html.j2` com margens, fontes, cores e estrutura medidas no original."""
    pagina = layout["pagina"]
    margens = pagina["margens_cm"]
    tipografia = layout["tipografia"]
    paragrafo = layout["paragrafo"]
    cores = layout["cores"]
    capa = layout["capa"]
    folha = layout.get("folha_de_rosto") or {}
    sumario = layout.get("sumario") or {}
    cabecalho = layout["cabecalho"]
    rodape = layout["rodape"]
    numeracao = rodape.get("numeracao_pagina") or {}
    fotos = layout["relatorio_fotografico"]
    legenda = fotos["legenda"]
    assinatura = layout.get("assinatura") or {}
    tabelas = _tabelas_por_chave(layout)
    blocos = _plano_de_secoes(layout)
    familia = tipografia["familia"]
    largura_util_pt = pagina["largura_pt"] - (margens["esquerda"] + margens["direita"]) * PT_POR_CM

    corpo = []
    for bloco in blocos:
        if bloco["tipo"] == "titulo":
            corpo.append(_html_titulo(bloco))
        elif bloco["tipo"] == "paragrafos":
            corpo.append(
                f"  {{% for paragrafo in conteudo.get('{bloco['chave']}', []) %}}<p>{{{{ paragrafo }}}}</p>{{% endfor %}}"
            )
        elif bloco["tipo"] == "tabela":
            corpo.append(_html_tabela(tabelas[bloco["chave"]]))
        elif bloco["tipo"] == "figuras":
            corpo.append(
                "  {% for figura in figuras %}\n"
                '  <figure class="figura">\n'
                '    {% if figura.foto_data_uri %}<img src="{{ figura.foto_data_uri }}" alt="Figura {{ figura.numero }}">{% endif %}\n'
                f"    <figcaption>{_legenda_modelo(layout)}</figcaption>\n"
                "  </figure>\n"
                "  {% endfor %}"
            )
        elif bloco["tipo"] == "sistemas":
            corpo.append(_html_sistemas(bloco))
        elif bloco["tipo"] == "assinatura":
            corpo.append(_html_assinatura(layout))
    corpo_html = "\n".join(corpo)

    linhas_rodape = "\n".join(
        f'    <div class="linha-rodape{" contato" if "email" in linha["modelo"] else ""}">{linha["modelo"]}</div>'
        for linha in rodape["linhas"]
    )
    logo_cabecalho = cabecalho.get("logo") or {}
    titulo_capa = capa["titulo"]
    estilos_capa = "\n".join(
        f"  .capa .e{indice} {{ font-family: \"{elemento['familia']}\", sans-serif; font-size: {elemento['fonte_pt']}pt; "
        f"font-weight: {'bold' if elemento['negrito'] else 'normal'}; color: {elemento['cor']}; }}"
        for indice, elemento in enumerate(capa["elementos"])
    )
    folha_titulo = folha.get("titulo") or {}
    folha_objeto = folha.get("objeto") or {}
    folha_data = folha.get("data") or {}
    recuos_sumario = sumario.get("recuo_por_nivel_cm") or {}
    altura_util_pt = pagina["altura_pt"] - (margens["superior"] + margens["inferior"]) * PT_POR_CM
    foto = fotos["foto"]
    contador_capa = "counter-increment: none;" if numeracao.get("deslocamento", 0) < 0 else ""

    return f"""<!DOCTYPE html>
{{#
  {CABECALHO_GERADO}

  Layout derivado do PDF original sha256 {layout['origem']['sha256'][:16]}…
  ({layout['origem']['paginas']} páginas medidas). O nome do arquivo não é versionado:
  identifica o cliente vistoriado (OWASP A02). Nenhum dado pessoal do exemplar entra
  aqui — responsável, obra, edificação, local e datas são placeholders.
#}}
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>{_e(' '.join(folha_titulo.get('linhas') or titulo_capa['linhas']))} — {{{{ edificacao.nome }}}}</title>
<style>
  @page {{
    size: {pagina['tamanho']} {pagina['orientacao']};
    margin: {margens['superior']}cm {margens['direita']}cm {margens['inferior']}cm {margens['esquerda']}cm;
    @top-right {{ content: element(cabecalho); vertical-align: top; }}
    @bottom-center {{ content: element(rodape); vertical-align: top; }}
    @bottom-right {{
      content: counter(page);
      font-family: "{numeracao.get('familia', familia)}", sans-serif;
      font-size: {numeracao.get('fonte_pt', 11)}pt;
      vertical-align: bottom;
    }}
  }}
  /* Capa sangrada, sem cabeçalho/rodapé e fora da contagem de páginas
     (deslocamento medido: {numeracao.get('deslocamento', 0)}). */
  @page capa {{
    margin: 0;
    {contador_capa}
    @top-right {{ content: none; }}
    @bottom-center {{ content: none; }}
    @bottom-right {{ content: none; }}
  }}
  body {{
    font-family: "{familia}", "DejaVu Serif", serif;
    font-size: {tipografia['corpo_pt']}pt;
    line-height: {paragrafo['altura_linha']};
    color: {cores['texto']};
    margin: 0;
  }}
  p {{ margin: 0 0 {paragrafo['espaco_entre_paragrafos_pt']}pt 0; text-align: {paragrafo['alinhamento']}; }}
  h1, h2, h3 {{ font-family: "{tipografia['familia_titulo']}", serif; font-weight: bold; margin: 12pt 0 8pt 0; }}
  h1 {{ font-size: {_fonte_do_nivel(layout, 1)}pt; margin-left: {_recuo_do_nivel(layout, 1)}cm; text-transform: uppercase; }}
  h2 {{ font-size: {_fonte_do_nivel(layout, 2)}pt; margin-left: {_recuo_do_nivel(layout, 2)}cm; }}
  h3 {{ font-size: {_fonte_do_nivel(layout, 3)}pt; margin-left: {_recuo_do_nivel(layout, 3)}cm; }}
  h1 {{ break-before: page; }}

  .cabecalho {{ position: running(cabecalho); text-align: right; padding-top: {logo_cabecalho.get('topo_pt', 0)}pt; }}
  .cabecalho img {{ width: {logo_cabecalho.get('largura_pt', 109)}pt; }}
  .rodape {{ position: running(rodape); text-align: center; }}
  .linha-rodape {{ font-family: "{(rodape['linhas'] or [{'familia': familia}])[0]['familia']}", serif; font-size: {(rodape['linhas'] or [{'fonte_pt': 10}])[0]['fonte_pt']}pt; line-height: 1.2; }}
  .linha-rodape.contato {{ color: {cores.get('rodape_contato') or cores['texto']}; }}

  .capa {{ page: capa; position: relative; width: {pagina['largura_pt']}pt; height: {pagina['altura_pt']}pt; overflow: hidden;
           background: {cores.get('capa_destaque') or '#333333'}; }}
  .capa .fundo {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; object-fit: cover; }}
  .capa .logo, .capa .titulo, .capa .elemento, .capa .faixa {{ position: absolute; }}
  .capa .titulo {{
    font-family: "{titulo_capa['familia']}", sans-serif;
    font-size: {titulo_capa['fonte_pt']}pt;
    font-weight: {'bold' if titulo_capa['negrito'] else 'normal'};
    line-height: {titulo_capa['entrelinha_pt']}pt;
    color: {titulo_capa['cor']};
  }}
  .capa .faixa {{ background: #FFFFFF; }}
{estilos_capa}

  .folha-rosto {{ position: relative; height: {round(altura_util_pt, 1)}pt; break-after: page; text-align: center; }}
  .folha-rosto > div {{ position: absolute; left: 0; right: 0; font-weight: bold; }}
  .folha-rosto .titulo {{ font-size: {folha_titulo.get('fonte_pt', 36)}pt; line-height: 1.3; }}
  .folha-rosto .objeto {{ font-size: {folha_objeto.get('fonte_pt', 36)}pt; line-height: 1.3; }}
  .folha-rosto .data {{ font-size: {folha_data.get('fonte_pt', 18)}pt; }}

  .sumario {{ break-after: page; }}
  .sumario .titulo-sumario {{ font-size: {sumario.get('titulo_pt') or 16}pt; font-weight: bold; margin-bottom: 12pt; }}
  .sumario ul {{ list-style: none; margin: 0; padding: 0; }}
  .sumario li {{ font-family: "{sumario.get('familia_entrada') or familia}", serif; font-size: {sumario.get('entrada_pt') or 11}pt;
                 font-weight: {'bold' if sumario.get('entrada_negrito', True) else 'normal'}; margin: 0 0 6pt 0; }}
  .sumario li.n2 {{ margin-left: {recuos_sumario.get('2', 0.39)}cm; }}
  .sumario li.n3 {{ margin-left: {recuos_sumario.get('3', 0.77)}cm; }}
  .sumario a {{ color: inherit; text-decoration: none; }}
  .sumario a::after {{ content: leader('.') target-counter(attr(href), page); }}

  /* Relatório fotográfico: {fotos['fotos_por_pagina']} fotos por página, na largura do texto. */
  figure.figura {{ margin: 0 0 12pt 0; break-inside: avoid; }}
  figure.figura img {{ display: block; width: {round(min(foto['largura_pt'], largura_util_pt), 1)}pt;
                       height: {foto['altura_pt']}pt; object-fit: contain; margin: 0 auto; }}
  figure.figura figcaption {{
    font-family: "{legenda['familia']}", sans-serif;
    font-size: {legenda['fonte_pt']}pt;
    font-style: {'italic' if legenda['italico'] else 'normal'};
    color: {legenda['cor']};
    margin-top: {legenda['afastamento_pt']}pt;
    line-height: 1.2;
    text-align: justify;
  }}

  table.tabela {{ width: 100%; border-collapse: collapse; margin: 6pt 0 12pt 0; }}
  table.tabela th, table.tabela td {{ border: 0.5pt solid #000000; padding: 2pt 4pt; vertical-align: top; text-align: left; }}
{_estilos_tabelas(tabelas)}

  .assinatura {{ margin-top: 24pt; text-align: {assinatura.get('alinhamento', 'right')}; break-inside: avoid;
                 font-family: "{assinatura.get('familia', familia)}", sans-serif; font-size: {assinatura.get('fonte_pt', 12)}pt; }}
  .assinatura .rubrica {{ width: {(assinatura.get('imagem_assinatura') or {}).get('largura_pt', 138)}pt; display: block; margin-left: auto; }}
  .assinatura .traco {{ border-top: 0.75pt solid #000000; width: {assinatura.get('linha_largura_pt', 287)}pt; margin: 0 0 2pt auto; }}
  .assinatura .nome {{ font-weight: {'bold' if assinatura.get('nome_negrito', True) else 'normal'}; }}
  .assinatura .local-data {{ margin-top: {(assinatura.get('local_data') or {}).get('afastamento_pt', 24)}pt; }}
</style>
</head>
<body>
  <div class="cabecalho">{{% if logo_data_uri %}}<img src="{_logo_cabecalho_data_uri()}" alt="Garra Engenharia">{{% endif %}}</div>
  <div class="rodape">
{linhas_rodape}
  </div>

{_html_capa(layout)}

{_html_folha_de_rosto(layout)}

{_html_sumario(layout, blocos)}

{corpo_html}
</body>
</html>
"""


def _estilos_tabelas(tabelas: dict[str, dict[str, Any]]) -> str:
    return "\n".join(
        f"  table.tabela-{chave} {{ font-family: \"{tabela['familia']}\", serif; font-size: {tabela['corpo_fonte_pt'] or 11}pt; }}\n"
        f"  table.tabela-{chave} th {{ background: {tabela['cabecalho_fundo']}; color: {tabela['cabecalho_cor_texto']}; "
        f"font-size: {tabela['cabecalho_fonte_pt']}pt; font-weight: {'bold' if tabela['cabecalho_negrito'] else 'normal'}; }}"
        for chave, tabela in tabelas.items()
    )


# --------------------------------------------------------------------------------------
# DOCX (docxtpl)
# --------------------------------------------------------------------------------------


def _rgb(cor: str | None):
    from docx.shared import RGBColor

    return RGBColor.from_string((cor or "#000000").lstrip("#").upper())


def _campo(paragrafo: Any, instrucao: str, texto_provisorio: str = "") -> None:
    """Insere um campo do Word (PAGE, TOC) — atualizado pelo Word ao abrir/imprimir."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    def caractere(tipo: str) -> Any:
        execucao = OxmlElement("w:r")
        marca = OxmlElement("w:fldChar")
        marca.set(qn("w:fldCharType"), tipo)
        execucao.append(marca)
        return execucao

    paragrafo._p.append(caractere("begin"))
    execucao = OxmlElement("w:r")
    codigo = OxmlElement("w:instrText")
    codigo.set(qn("xml:space"), "preserve")
    codigo.text = f" {instrucao} "
    execucao.append(codigo)
    paragrafo._p.append(execucao)
    paragrafo._p.append(caractere("separate"))
    provisorio = OxmlElement("w:r")
    texto = OxmlElement("w:t")
    texto.text = texto_provisorio
    provisorio.append(texto)
    paragrafo._p.append(provisorio)
    paragrafo._p.append(caractere("end"))


def _sombrear(celula: Any, cor: str) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    sombreamento = OxmlElement("w:shd")
    sombreamento.set(qn("w:val"), "clear")
    sombreamento.set(qn("w:color"), "auto")
    sombreamento.set(qn("w:fill"), cor.lstrip("#").upper())
    celula._tc.get_or_add_tcPr().append(sombreamento)


def _numeracao_inicial(secao: Any, inicio: int) -> None:
    """`<w:pgNumType w:start>` na posição exigida pelo schema de `w:sectPr`."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    sect_pr = secao._sectPr
    elemento = OxmlElement("w:pgNumType")
    elemento.set(qn("w:start"), str(inicio))
    seguinte = next(
        (filho for filho in sect_pr if filho.tag in {qn("w:cols"), qn("w:formProt"), qn("w:vAlign"), qn("w:titlePg"), qn("w:docGrid")}),
        None,
    )
    if seguinte is not None:
        seguinte.addprevious(elemento)
    else:
        sect_pr.append(elemento)


def _normalizar_zip(destino: Path) -> None:
    """Regrava o DOCX com data fixa em cada entrada: mesma entrada, mesmos bytes."""
    with zipfile.ZipFile(destino) as original:
        entradas = [(info.filename, original.read(info.filename)) for info in original.infolist()]
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as normalizado:
        for nome, conteudo in entradas:
            info = zipfile.ZipInfo(nome, date_time=DATA_FIXA.timetuple()[:6])
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            normalizado.writestr(info, conteudo)
    destino.write_bytes(buffer.getvalue())


def gerar_docx(layout: dict[str, Any], destino: Path) -> None:
    """Monta o `.docx` com as mesmas seções, rótulos e placeholders do HTML."""
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.shared import Cm, Pt

    alinhamentos = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
    }
    pagina = layout["pagina"]
    margens = pagina["margens_cm"]
    tipografia = layout["tipografia"]
    paragrafo_medido = layout["paragrafo"]
    cores = layout["cores"]
    capa = layout["capa"]
    rodape = layout["rodape"]
    numeracao = rodape.get("numeracao_pagina") or {}
    legenda = layout["relatorio_fotografico"]["legenda"]
    assinatura = layout.get("assinatura") or {}
    tabelas = _tabelas_por_chave(layout)
    largura_util_cm = pagina["largura_pt"] / PT_POR_CM - margens["esquerda"] - margens["direita"]

    documento = Document()
    propriedades = documento.core_properties
    # Só propriedades `dc:`/`dcterms:`: com o docxtpl carregado no mesmo processo, o
    # prefixo `cp:` é remapeado e `last_modified_by`/`revision` sairiam duplicados.
    propriedades.author = "Garra Engenharia"
    propriedades.title = " ".join((layout.get("folha_de_rosto") or {}).get("titulo", {}).get("linhas") or capa["titulo"]["linhas"])
    propriedades.created = propriedades.modified = DATA_FIXA.replace(tzinfo=None)

    normal = documento.styles["Normal"]
    normal.font.name = tipografia["familia"]
    normal.font.size = Pt(tipografia["corpo_pt"])
    normal.font.color.rgb = _rgb(cores["texto"])
    normal.paragraph_format.line_spacing = Pt(paragrafo_medido["entrelinha_pt"])
    normal.paragraph_format.space_after = Pt(paragrafo_medido["espaco_entre_paragrafos_pt"])
    normal.paragraph_format.alignment = alinhamentos[paragrafo_medido["alinhamento"]]
    for nivel in (1, 2, 3):
        estilo = documento.styles[f"Heading {nivel}"]
        estilo.font.name = tipografia["familia_titulo"]
        estilo.font.size = Pt(_fonte_do_nivel(layout, nivel))
        estilo.font.bold = True
        estilo.font.italic = False
        estilo.font.color.rgb = _rgb(cores["texto"])
        estilo.paragraph_format.left_indent = Cm(_recuo_do_nivel(layout, nivel))
        estilo.paragraph_format.space_before = Pt(12)
        estilo.paragraph_format.space_after = Pt(8)
        estilo.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    def paragrafo(texto: str = "", *, alinhamento: str | None = None, tamanho: float | None = None,
                  negrito: bool = False, italico: bool = False, cor: str | None = None,
                  familia: str | None = None) -> Any:
        novo = documento.add_paragraph()
        if alinhamento:
            novo.alignment = alinhamentos[alinhamento]
        if texto:
            execucao = novo.add_run(texto)
            execucao.bold = negrito or None
            execucao.italic = italico or None
            if tamanho:
                execucao.font.size = Pt(tamanho)
            if cor:
                execucao.font.color.rgb = _rgb(cor)
            if familia:
                execucao.font.name = familia
        return novo

    def laco(abertura: str, corpo: str, **estilo: Any) -> None:
        paragrafo(f"{{%p {abertura} %}}")
        paragrafo(corpo, **estilo)
        paragrafo("{%p endfor %}")

    # --- Seção 1: capa (sem cabeçalho/rodapé, fora da numeração) ---------------------
    capa_secao = documento.sections[0]
    capa_secao.page_width = Pt(pagina["largura_pt"])
    capa_secao.page_height = Pt(pagina["altura_pt"])
    for lado in ("left_margin", "right_margin"):
        setattr(capa_secao, lado, Pt(capa["titulo"]["x_pt"]))
    capa_secao.top_margin = Cm(1)
    capa_secao.bottom_margin = Cm(1)
    if LOGO_PNG.is_file():
        largura_logo = (capa.get("logo") or {}).get("largura_pt") or 216
        paragrafo(alinhamento="center").add_run().add_picture(str(LOGO_PNG), width=Pt(largura_logo))
    titulo_capa = capa["titulo"]
    # Sem a arte de fundo do PDF, o branco medido sumiria no papel: usa-se a cor de destaque.
    cor_titulo_docx = cores.get("capa_destaque") if (titulo_capa["cor"] or "").upper() == "#FFFFFF" else titulo_capa["cor"]
    for linha in titulo_capa["linhas"]:
        paragrafo(linha, tamanho=titulo_capa["fonte_pt"], negrito=titulo_capa["negrito"], cor=cor_titulo_docx,
                  familia=titulo_capa["familia"]).paragraph_format.space_after = Pt(0)
    for elemento in capa["elementos"]:
        cor = cores.get("capa_destaque") if (elemento["cor"] or "").upper() == "#FFFFFF" else elemento["cor"]
        for linha in elemento["linhas"]:
            paragrafo(linha, alinhamento=elemento["alinhamento"], tamanho=elemento["fonte_pt"],
                      negrito=elemento["negrito"], cor=cor, familia=elemento["familia"]).paragraph_format.space_after = Pt(0)
        paragrafo()

    # --- Seção 2: corpo, com cabeçalho (logo) e rodapé medidos ------------------------
    corpo_secao = documento.add_section(WD_SECTION.NEW_PAGE)
    corpo_secao.left_margin = Cm(margens["esquerda"])
    corpo_secao.right_margin = Cm(margens["direita"])
    corpo_secao.top_margin = Cm(margens["superior"])
    corpo_secao.bottom_margin = Cm(margens["inferior"])
    corpo_secao.header_distance = Pt((layout["cabecalho"].get("logo") or {}).get("topo_pt") or 12)
    corpo_secao.footer_distance = Pt(max(pagina["altura_pt"] - (numeracao.get("topo_pt") or pagina["altura_pt"]) - 12, 6))
    corpo_secao.header.is_linked_to_previous = False
    corpo_secao.footer.is_linked_to_previous = False
    # Página física 2 recebe o número 2 + deslocamento (medido: capa fora da contagem).
    _numeracao_inicial(corpo_secao, max(2 + int(numeracao.get("deslocamento", 0)), 0))

    cabecalho = corpo_secao.header.paragraphs[0]
    cabecalho.alignment = alinhamentos[(layout["cabecalho"].get("logo") or {}).get("alinhamento", "right")]
    if LOGO_PNG.is_file() and layout["cabecalho"].get("logo"):
        cabecalho.add_run().add_picture(str(LOGO_PNG), width=Pt(layout["cabecalho"]["logo"]["largura_pt"]))

    rodape_paragrafos = corpo_secao.footer.paragraphs
    for posicao, linha in enumerate(rodape["linhas"]):
        alvo = rodape_paragrafos[0] if posicao == 0 else corpo_secao.footer.add_paragraph()
        alvo.alignment = alinhamentos[linha["alinhamento"]]
        alvo.paragraph_format.space_after = Pt(0)
        alvo.paragraph_format.line_spacing = 1.0
        execucao = alvo.add_run(linha["modelo"])
        execucao.font.size = Pt(linha["fonte_pt"])
        execucao.font.name = linha["familia"]
        execucao.font.color.rgb = _rgb(linha["cor"])
    if numeracao:
        numero = corpo_secao.footer.add_paragraph()
        numero.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        numero.paragraph_format.space_after = Pt(0)
        _campo(numero, "PAGE", "1")
        for execucao in numero.runs:
            execucao.font.size = Pt(numeracao["fonte_pt"])
            execucao.font.name = numeracao["familia"]

    # Folha de rosto
    folha = layout.get("folha_de_rosto")
    if folha:
        titulo = folha["titulo"]
        topo_util = margens["superior"] * PT_POR_CM
        primeiro = paragrafo(alinhamento=titulo["alinhamento"])
        primeiro.paragraph_format.space_before = Pt(max(titulo["topo_pt"] - topo_util, 0))
        primeiro.add_run("\n".join(titulo["linhas"])).bold = titulo["negrito"]
        primeiro.runs[0].font.size = Pt(titulo["fonte_pt"])
        for papel in ("objeto", "data"):
            item = folha.get(papel)
            if item:
                alvo = paragrafo(item["modelo"], alinhamento=item["alinhamento"], tamanho=item["fonte_pt"], negrito=item["negrito"])
                alvo.paragraph_format.space_before = Pt(48)
        documento.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # Sumário: campo TOC sobre os estilos de título (o Word preenche ao atualizar campos).
    sumario = layout.get("sumario") or {}
    paragrafo(sumario.get("titulo") or "SUMÁRIO", tamanho=sumario.get("titulo_pt") or 16, negrito=True)
    _campo(paragrafo(), 'TOC \\o "1-3" \\h \\z \\u', "Atualize o sumário (F9) após gerar o documento.")
    documento.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def titulo_docx(texto: str, nivel: int) -> None:
        documento.add_heading(texto, level=nivel)

    for bloco in _plano_de_secoes(layout):
        if bloco["tipo"] == "titulo":
            texto = f"{bloco['numero']}. {bloco['texto']}"
            complemento = bloco.get("complemento")
            if complemento:
                chave = complemento["chave"]
                texto += (
                    f"{{% if complementos.get('{chave}') %}} {complemento['separador']} "
                    f"{{{{ complementos.get('{chave}') }}}}{{% endif %}}"
                )
            titulo_docx(texto, bloco["nivel"])
        elif bloco["tipo"] == "paragrafos":
            laco(f"for paragrafo in conteudo.get('{bloco['chave']}', [])", "{{ paragrafo }}")
        elif bloco["tipo"] == "tabela":
            tabela = tabelas[bloco["chave"]]
            colunas = tabela["colunas"]
            # 4 linhas: cabeçalho, `{%tr for %}`, dados, `{%tr endfor %}` — o `{%tr %}`
            # remove a linha inteira em que aparece (armadilha do docxtpl).
            grade = documento.add_table(rows=4, cols=len(colunas))
            grade.style = "Table Grid"
            grade.alignment = WD_TABLE_ALIGNMENT.CENTER
            for posicao, coluna in enumerate(colunas):
                largura = Cm(round(largura_util_cm * coluna["largura_pct"] / 100, 2))
                for linha in grade.rows:
                    linha.cells[posicao].width = largura
                celula = grade.rows[0].cells[posicao]
                _sombrear(celula, tabela["cabecalho_fundo"])
                execucao = celula.paragraphs[0].add_run(coluna["rotulo"])
                execucao.bold = tabela["cabecalho_negrito"]
                execucao.font.size = Pt(tabela["cabecalho_fonte_pt"])
                execucao.font.color.rgb = _rgb(tabela["cabecalho_cor_texto"])
                grade.rows[2].cells[posicao].text = f"{{{{ linha.{coluna['chave']} }}}}"
            grade.rows[1].cells[0].text = f"{{%tr for linha in tabelas.get('{tabela['chave']}', []) %}}"
            grade.rows[3].cells[0].text = "{%tr endfor %}"
        elif bloco["tipo"] == "figuras":
            paragrafo("{%p for figura in figuras %}")
            paragrafo("{{ figura.imagem }}", alinhamento="center")
            paragrafo(_legenda_modelo(layout), alinhamento="justify", tamanho=legenda["fonte_pt"],
                      italico=legenda["italico"], cor=legenda["cor"], familia=legenda["familia"])
            paragrafo("{%p endfor %}")
        elif bloco["tipo"] == "sistemas":
            numero = bloco["numero"]
            paragrafo("{%p for sistema in sistemas %}")
            titulo_docx(f"{numero}.{{{{ loop.index }}}}. {{{{ sistema.nome }}}}", 2)
            for ordem, rotulo in enumerate(bloco["rotulos"], start=1):
                titulo_docx(f"{numero}.{{{{ loop.index }}}}.{ordem}. {rotulo['titulo']}", 3)
                laco(f"for paragrafo in sistema.get('{rotulo['chave']}', [])", "{{ paragrafo }}")
            paragrafo("{%p endfor %}")
        elif bloco["tipo"] == "assinatura":
            estilo = {
                "alinhamento": assinatura["alinhamento"],
                "tamanho": assinatura["fonte_pt"],
                "familia": assinatura["familia"],
            }
            paragrafo("{%p if assinatura_imagem %}")
            paragrafo("{{ assinatura_imagem }}", alinhamento=assinatura["alinhamento"])
            paragrafo("{%p endif %}")
            traco = "_" * max(round(assinatura["linha_largura_pt"] / LARGURA_SUBLINHADO_PT), 10)
            paragrafo(traco, **estilo).paragraph_format.space_after = Pt(0)
            for modelo in assinatura["linhas"]:
                alvo = paragrafo(modelo, negrito=assinatura["nome_negrito"] and modelo == "{{ responsavel.nome }}", **estilo)
                alvo.paragraph_format.space_after = Pt(0)
            paragrafo("{%p for linha in responsavel.qualificacoes %}")
            paragrafo("{{ linha }}", **estilo).paragraph_format.space_after = Pt(0)
            paragrafo("{%p endfor %}")
            local_data = assinatura.get("local_data")
            if local_data:
                alvo = paragrafo(local_data["modelo"], **{**estilo, "alinhamento": local_data["alinhamento"]})
                alvo.paragraph_format.space_before = Pt(local_data["afastamento_pt"])

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(destino)
    _normalizar_zip(destino)


def _carregar_layout(original: Path | None) -> dict[str, Any]:
    if original is not None:
        return extrair_layout(original)
    if not LAYOUT_JSON.is_file():
        raise LayoutExtractionError(
            f"{LAYOUT_JSON} não existe e nenhum --original foi informado. "
            "Rode uma vez com o PDF do cliente para gerar o layout."
        )
    return json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera os templates da Vistoria Cautelar a partir do PDF original.")
    parser.add_argument("--original", type=Path, default=None, help="Caminho do PDF original do laudo.")
    argumentos = parser.parse_args(argv)

    try:
        layout = _carregar_layout(argumentos.original)
    except LayoutExtractionError as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    if argumentos.original is not None:
        layout["gerado_em"] = datetime.now(UTC).isoformat(timespec="seconds")
        LAYOUT_JSON.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"layout.json atualizado a partir do original informado (sha256 {layout['origem']['sha256'][:16]}…)")

    HTML_TEMPLATE.write_text(gerar_html(layout), encoding="utf-8", newline="\n")
    gerar_docx(layout, DOCX_TEMPLATE)
    print(f"gerados: {HTML_TEMPLATE.name}, {DOCX_TEMPLATE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
