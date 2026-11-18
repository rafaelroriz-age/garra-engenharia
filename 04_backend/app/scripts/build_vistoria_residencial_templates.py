"""Deriva os templates da Vistoria Residencial (HTML/Jinja2 + DOCX) a partir do PDF original.

Pipeline determinístico de ADR-13/DEC-25, irmão de `build_ltip_templates`:

    01_output-context/Laudo Técnico de Vistoria de Imóvel Residencial - <unidade>.pdf
        -> app/scripts/vistoria_residencial_layout_extractor.extrair_layout()
        -> 04_backend/templates/vistoria_residencial/layout.json                 (versionado)
        -> .../vistoria_residencial/vistoria_residencial_template.html.j2      (WeasyPrint, ADR-01)
        -> .../vistoria_residencial/vistoria_residencial_template.docx         (docxtpl, ADR-04)

Uso:

    python -m app.scripts.build_vistoria_residencial_templates \
        --original "../01_output-context/Laudo Técnico de Vistoria de Imóvel Residencial - Ap. 1404.pdf"

Sem `--original`, reutiliza o `layout.json` já versionado (máquinas e CI sem o
original do cliente). As duas saídas dependem **só** do `layout.json` e dos
assets de marca (`templates/assets/`): a mesma entrada gera a mesma saída.

Contexto esperado pelos dois templates (montado pelo pipeline de renderização,
tarefa à parte — ver `rfo_pipeline.py`):

- `fiscal`: `nome`, `crea`, `email`, `telefone`, `qualificacoes` (lista de linhas);
- `imovel.unidade` e `edificacao`: `nome`, `endereco`;
- `data_emissao`, `local_emissao`;
- `textos`: dicionário `{"s1_1": [parágrafos], ...}` — chave de cada seção fixa
  (ver `chave_secao()`); seção sem texto fica só com o título;
- `fotos`: lista de `{numero, legenda, fonte, data_uri | imagem}` (HTML usa
  `data_uri`; DOCX usa `imagem`, um `docxtpl.InlineImage`);
- `sistemas`: lista de `{nome, <chave de cada subtítulo>: [itens]}`;
- `logo_data_uri`, `capa_fundo_data_uri`, `assinatura_data_uri` (opcionais, HTML).
  `logo_data_uri` (o SVG) só entra na capa; no cabeçalho corrido ele apenas liga o
  logo, que sai do PNG embutido no template (DEC-54, ver `_logo_cabecalho_data_uri`).
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import sys
from html import escape
from pathlib import Path
from typing import Any

from app.scripts.vistoria_residencial_layout_extractor import (
    LayoutExtractionError,
    extrair_layout,
)

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates" / "vistoria_residencial"
LAYOUT_JSON = TEMPLATES_DIR / "layout.json"
HTML_TEMPLATE = TEMPLATES_DIR / "vistoria_residencial_template.html.j2"
DOCX_TEMPLATE = TEMPLATES_DIR / "vistoria_residencial_template.docx"
ASSETS_DIR = TEMPLATES_DIR.parent / "assets"
# Marca com fundo transparente (RN-07/ADR-16), gerada por `build_brand_assets`;
# o DOCX não aceita SVG.
LOGO_PNG = ASSETS_DIR / "logo-garra.png"
MARCA_JSON = ASSETS_DIR / "marca.json"

PT_EM_CM = 2.54 / 72
#: Data fixa gravada nas propriedades do DOCX, para a saída não variar entre execuções.
DATA_FIXA_DOCX = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)

CABECALHO_GERADO = (
    "ARQUIVO GERADO — não editar à mão. "
    "Produzido por `python -m app.scripts.build_vistoria_residencial_templates` a partir de "
    "templates/vistoria_residencial/layout.json (ADR-13/DEC-25)."
)

#: Variáveis de contexto que os dois templates precisam expor (verificado nos testes).
PLACEHOLDERS = (
    "fiscal.nome",
    "fiscal.crea",
    "fiscal.email",
    "fiscal.telefone",
    "fiscal.qualificacoes",
    "imovel.unidade",
    "edificacao.nome",
    "data_emissao",
    "local_emissao",
    "textos",
    "fotos",
    "sistemas",
)


def chave_secao(numero: str) -> str:
    """`4.2.1.` -> `s4_2_1` (chave em `textos`)."""
    return "s" + numero.rstrip(".").replace(".", "_")


def cor_de_fundo_da_capa() -> str:
    """Cor escura da marca (`marca.json`), usada na capa quando não há foto de fundo."""
    if MARCA_JSON.is_file():
        paleta = json.loads(MARCA_JSON.read_text(encoding="utf-8")).get("paleta", {})
        if paleta.get("escuro"):
            return paleta["escuro"]
    return "#000000"


def _capitulos(layout: dict[str, Any]) -> list[dict[str, Any]]:
    """Agrupa a lista plana de seções em capítulos (nível 1 + subseções)."""
    capitulos: list[dict[str, Any]] = []
    for secao in layout["secoes"]:
        if secao["nivel"] == 1 or not capitulos:
            capitulos.append({**secao, "subsecoes": []})
        else:
            capitulos[-1]["subsecoes"].append(secao)
    return capitulos


def _fonte_do_nivel(layout: dict[str, Any], nivel: int) -> float:
    for titulo in layout.get("titulos", []):
        if titulo["nivel"] == nivel:
            return titulo["fonte_pt"]
    return layout["tipografia"]["titulo_pt"] if nivel <= 2 else layout["tipografia"]["corpo_pt"]


def _cm(pt: float) -> float:
    return round(pt * PT_EM_CM, 2)


# --------------------------------------------------------------------------- HTML


def _html_paragrafos(numero: str) -> str:
    return f"{{% for paragrafo in textos.{chave_secao(numero)} %}}<p>{{{{ paragrafo }}}}</p>{{% endfor %}}"


def _html_fotos(layout: dict[str, Any]) -> str:
    legenda = layout["relatorio_fotografico"]["legenda"]
    fonte_padrao = escape(legenda["fonte_padrao"] or "Autor")
    return (
        "    <div class=\"fotos\">\n"
        "    {% for foto in fotos %}\n"
        "      <figure class=\"foto\">\n"
        "        {% if foto.data_uri %}<img src=\"{{ foto.data_uri }}\" "
        f"alt=\"{legenda['rotulo']} {{{{ foto.numero }}}}\">{{% endif %}}\n"
        f"        <figcaption>{legenda['rotulo']} {{{{ foto.numero }}}} {legenda['separador']} "
        f"{{{{ foto.legenda }}}}. Fonte: {{{{ foto.fonte or \"{fonte_padrao}\" }}}}.</figcaption>\n"
        "      </figure>\n"
        "    {% endfor %}\n"
        "    </div>"
    )


def _html_sistemas(layout: dict[str, Any], numero: str) -> str:
    analise = layout["analise_por_sistema"]
    marcador = analise["marcador"] or ""
    blocos = []
    for subtitulo in analise["subtitulos"]:
        chave = subtitulo["chave"]
        if subtitulo["lista"]:
            corpo = (
                f"<ul>{{% for item in sistema.{chave} %}}<li>{{{{ item }}}}</li>{{% endfor %}}</ul>"
            )
        else:
            corpo = f"{{% for item in sistema.{chave} %}}<p>{{{{ item }}}}</p>{{% endfor %}}"
        blocos.append(
            f"      <h4 class=\"subtitulo\">{marcador} {escape(subtitulo['rotulo'])}</h4>\n      {corpo}"
        )
    return (
        "    {% for sistema in sistemas %}\n"
        "    <section class=\"sistema\">\n"
        f"      <h2>{numero}{{{{ loop.index }}}}. {{{{ sistema.nome }}}}</h2>\n"
        + "\n".join(blocos)
        + "\n    </section>\n"
        "    {% endfor %}"
    )


def _html_assinatura() -> str:
    return (
        "    <div class=\"assinatura\">\n"
        "      {% if assinatura_data_uri %}<img class=\"rubrica\" src=\"{{ assinatura_data_uri }}\" alt=\"Assinatura\">{% endif %}\n"
        "      <div class=\"linha-assinatura\"></div>\n"
        "      <div class=\"nome\">{{ fiscal.nome }}</div>\n"
        "      <div>Eng. Civil - CREA nº {{ fiscal.crea }}</div>\n"
        "      {% for qualificacao in fiscal.qualificacoes %}<div>{{ qualificacao }}</div>{% endfor %}\n"
        "      <div class=\"local-data\">{{ local_emissao }}, {{ data_emissao }}.</div>\n"
        "    </div>"
    )


def _html_capitulos(layout: dict[str, Any]) -> str:
    assinatura = layout.get("assinatura") or {}
    partes = []
    for capitulo in _capitulos(layout):
        linhas = [
            "  <section class=\"capitulo\">",
            f"    <h1>{capitulo['numero']} {escape(capitulo['titulo'])}</h1>",
            f"    {_html_paragrafos(capitulo['numero'])}",
        ]
        for secao in capitulo["subsecoes"]:
            nivel = min(secao["nivel"], 4)
            linhas.append(f"    <h{nivel}>{secao['numero']} {escape(secao['titulo'])}</h{nivel}>")
            linhas.append(f"    {_html_paragrafos(secao['numero'])}")
        if capitulo["tipo"] == "fotografico":
            linhas.append(_html_fotos(layout))
        elif capitulo["tipo"] == "por_sistema":
            linhas.append(_html_sistemas(layout, capitulo["numero"]))
        if assinatura.get("secao") == capitulo["numero"]:
            linhas.append(_html_assinatura())
        linhas.append("  </section>")
        partes.append("\n".join(linhas))
    return "\n\n".join(partes)


def _logo_cabecalho_data_uri() -> str:
    """PNG da marca como data URI, para o logo do cabeçalho corrido (DEC-54).

    O WeasyPrint 70 redesenha o SVG vetorizado (76 KB) em cada página de um
    elemento `running()`: ~24 s em 200 páginas (T76). O PNG de `build_brand_assets`
    tem a mesma arte e 600 px de largura (≈ 400 dpi nos 3,86 cm do cabeçalho).
    Embutido no template porque o `url_fetcher` dos pipelines só resolve `data:`
    e as fotos registradas (DEC-41).
    """
    if not LOGO_PNG.is_file():
        raise FileNotFoundError(f"{LOGO_PNG} não existe: rode `python -m app.scripts.build_brand_assets`.")
    return "data:image/png;base64," + base64.b64encode(LOGO_PNG.read_bytes()).decode("ascii")


def gerar_html(layout: dict[str, Any]) -> str:
    """Monta o `.html.j2` com as margens, fontes, cabeçalho, rodapé e grade medidos no original."""
    pagina = layout["pagina"]
    margens = pagina["margens_cm"]
    tipografia = layout["tipografia"]
    cores = layout["cores"]
    capa = layout["capa"]
    rosto = layout.get("folha_de_rosto")
    cabecalho = layout["cabecalho"]["logo"]
    rodape = layout["rodape"]
    numeracao = rodape.get("numeracao_pagina") or {}
    fotos = layout["relatorio_fotografico"]
    legenda = fotos["legenda"]
    assinatura = layout.get("assinatura") or {}
    familia = tipografia["familia"]
    secundarios = capa.get("corpos_secundarios_pt") or [tipografia["titulo_pt"]]
    corpo_identificacao = secundarios[0]
    corpo_responsavel = secundarios[-1]
    largura_foto = round(100 / max(fotos["colunas"], 1) - 1, 2) if fotos["colunas"] > 1 else None
    logo_capa = capa.get("logo")
    rubrica = assinatura.get("rubrica") or {}

    linhas_rodape = []
    for papel, texto in zip(rodape["papeis"], rodape["linhas"], strict=True):
        classe = " class=\"contato\"" if papel == "contato" else ""
        linhas_rodape.append(f"    <div{classe}>{texto}</div>")
    rodape_html = "\n".join(linhas_rodape)

    rosto_html = ""
    if rosto:
        titulo_rosto = "<br>".join(escape(linha) for linha in rosto["titulo"]["linhas"])
        data_rosto = (rosto.get("data") or {}).get("fonte_pt", tipografia["titulo_pt"])
        rosto_html = f"""
  <section class="rosto">
    <div class="titulo">{titulo_rosto}</div>
    <div class="identificacao">{{{{ imovel.unidade }}}}<br>{{{{ edificacao.nome }}}}</div>
    <div class="data" style="font-size: {data_rosto}pt">{{{{ data_emissao }}}}</div>
  </section>
"""
    titulo_capa = "<br>".join(escape(linha) for linha in capa["titulo"].get("linhas") or [capa["titulo"]["texto"]])
    rotulo_responsavel = escape(capa.get("rotulo_responsavel") or "RESP. TÉCNICO:")

    return f"""<!DOCTYPE html>
{{#
  {CABECALHO_GERADO}

  Layout derivado do PDF original sha256 {layout['origem']['sha256'][:16]}…
  ({layout['origem']['paginas']} páginas medidas). O nome do arquivo não é versionado:
  identifica a unidade vistoriada (OWASP A02).
#}}
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>{escape(capa['titulo']['texto'])} — {{{{ imovel.unidade }}}}</title>
<style>
  @page {{
    size: {pagina['tamanho']} {pagina['orientacao']};
    margin: {margens['superior']}cm {margens['direita']}cm {margens['inferior']}cm {margens['esquerda']}cm;
    @top-right {{ content: element(cabecalho); vertical-align: top; }}
    @bottom-center {{ content: element(rodape); vertical-align: top; }}
    @bottom-right {{
      content: counter(page);
      font-family: {numeracao.get('familia') or familia}, sans-serif;
      font-size: {numeracao.get('fonte_pt') or rodape['fonte_pt']}pt;
    }}
  }}
  @page capa {{
    margin: 0;
    @top-right {{ content: none; }}
    @bottom-center {{ content: none; }}
    @bottom-right {{ content: none; }}
  }}
  body {{
    font-family: {familia}, "DejaVu Serif", serif;
    font-size: {tipografia['corpo_pt']}pt;
    color: {cores['texto']};
    margin: 0;
    text-align: justify;
  }}
  .cabecalho {{ position: running(cabecalho); text-align: right; padding-top: {_cm(cabecalho['topo_pt']) if cabecalho else 0}cm; }}
  .cabecalho img {{ width: {_cm(cabecalho['largura_pt']) if cabecalho else 3.86}cm; }}
  .rodape {{
    position: running(rodape);
    text-align: center;
    font-family: {rodape['familia'] or familia}, serif;
    font-size: {rodape['fonte_pt']}pt;
    line-height: 1.2;
  }}
  .rodape .contato {{ color: {cores.get('link') or cores['texto']}; }}
  h1 {{ font-size: {_fonte_do_nivel(layout, 1)}pt; font-weight: bold; text-transform: uppercase; margin: 0 0 0.4cm 0; }}
  h2 {{ font-size: {_fonte_do_nivel(layout, 2)}pt; font-weight: bold; margin: 0.4cm 0 0.2cm 0; }}
  h3 {{ font-size: {_fonte_do_nivel(layout, 3)}pt; font-weight: bold; margin: 0.3cm 0 0.15cm 0; }}
  h4 {{ font-size: {_fonte_do_nivel(layout, 4)}pt; font-weight: bold; margin: 0.3cm 0 0.15cm 0; }}
  p {{ margin: 0 0 0.3cm 0; line-height: 1.35; }}
  .capitulo {{ page-break-before: always; }}
  /* Capa: foto de fundo sangrada, logo no canto e texto em {capa['cor_texto']}. */
  .capa {{
    page: capa;
    position: relative;
    width: {pagina['largura_pt']}pt;
    height: {pagina['altura_pt']}pt;
    color: {capa['cor_texto']};
    background: {cor_de_fundo_da_capa()};
    font-family: {capa['titulo']['familia']}, "Open Sans", sans-serif;
    font-weight: bold;
    overflow: hidden;
  }}
  .capa .fundo {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  .capa .logo {{
    position: absolute;
    left: {logo_capa['x_pt'] if logo_capa else 0}pt;
    top: {max(logo_capa['topo_pt'], 0) if logo_capa else 0}pt;
    width: {logo_capa['largura_pt'] if logo_capa else 216}pt;
  }}
  .capa .titulo {{ position: absolute; top: 3.9cm; left: 1cm; width: 14.5cm; text-align: center; font-size: {capa['titulo']['fonte_pt']}pt; line-height: 1.15; }}
  .capa .identificacao {{ position: absolute; top: 9.4cm; left: 1cm; width: 14.5cm; text-align: center; font-size: {corpo_identificacao}pt; }}
  .capa .responsavel {{ position: absolute; bottom: 0.9cm; left: 1cm; width: 19cm; font-size: {corpo_responsavel}pt; }}
  /* Folha de rosto: título em bloco, identificação do imóvel e data. */
  .rosto {{ text-align: center; font-weight: bold; }}
  .rosto .titulo, .rosto .identificacao {{
    font-size: {rosto['titulo']['fonte_pt'] if rosto else tipografia['titulo_pt']}pt;
    line-height: 1.3;
  }}
  .rosto .titulo {{ margin-top: 1.5cm; }}
  .rosto .identificacao {{ margin-top: 2.5cm; }}
  .rosto .data {{ margin-top: 4.5cm; }}
  /* Relatório fotográfico: {fotos['fotos_por_pagina']} figura(s) por página em {fotos['colunas']} coluna(s). */
  .fotos {{ {'display: flex; flex-wrap: wrap; gap: 0.3cm;' if largura_foto else ''} }}
  figure.foto {{ margin: 0.4cm auto; text-align: center; page-break-inside: avoid; {f'width: {largura_foto}%;' if largura_foto else ''} }}
  figure.foto img {{ width: {fotos['foto_largura_cm']}cm; height: {fotos['foto_altura_cm']}cm; object-fit: cover; }}
  figure.foto figcaption {{
    font-family: {legenda['familia'] or familia}, sans-serif;
    font-size: {legenda['fonte_pt']}pt;
    font-style: {'italic' if legenda['italico'] else 'normal'};
    color: {legenda['cor']};
    margin-top: 0.1cm;
  }}
  /* Análise por sistema: subtítulos fixos repetidos em cada sistema. */
  .sistema h4.subtitulo {{ font-size: {layout['analise_por_sistema']['fonte_pt']}pt; }}
  /* Bloco de assinatura do responsável técnico (RN-07). */
  .assinatura {{
    text-align: {'right' if assinatura.get('alinhamento') == 'direita' else 'center'};
    font-family: {assinatura.get('familia') or familia}, sans-serif;
    font-size: {assinatura.get('fonte_pt') or tipografia['corpo_pt']}pt;
    margin-top: 2cm;
    page-break-inside: avoid;
  }}
  .assinatura .rubrica {{ width: {rubrica.get('largura_pt', 138)}pt; height: {rubrica.get('altura_pt', 80)}pt; }}
  .assinatura .linha-assinatura {{ border-top: 0.75pt solid {cores['texto']}; width: 10cm; margin: 0 0 0.1cm auto; }}
  .assinatura .nome {{ font-weight: {'bold' if assinatura.get('nome_negrito', True) else 'normal'}; }}
  .assinatura .local-data {{ margin-top: 3cm; }}
</style>
</head>
<body>
  <div class="cabecalho">{{% if logo_data_uri %}}<img src="{_logo_cabecalho_data_uri()}" alt="Garra Engenharia">{{% endif %}}</div>
  <div class="rodape">
{rodape_html}
  </div>

  <section class="capa">
    {{% if capa_fundo_data_uri %}}<img class="fundo" src="{{{{ capa_fundo_data_uri }}}}" alt="">{{% endif %}}
    {{% if logo_data_uri %}}<img class="logo" src="{{{{ logo_data_uri }}}}" alt="Garra Engenharia">{{% endif %}}
    <div class="titulo">{titulo_capa}</div>
    <div class="identificacao">{{{{ imovel.unidade }}}}<br>{{{{ edificacao.nome }}}}</div>
    <div class="responsavel">
      {rotulo_responsavel}<br>
      ENG. CIVIL {{{{ fiscal.nome|upper }}}}<br>
      {{{{ data_emissao|upper }}}} &nbsp; CREA: {{{{ fiscal.crea }}}}
    </div>
  </section>
{rosto_html}
{_html_capitulos(layout)}
</body>
</html>
"""


# --------------------------------------------------------------------------- DOCX


def _campo_pagina(paragrafo: Any) -> None:
    """Insere o campo PAGE do Word (numeração automática) no parágrafo."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    campo = OxmlElement("w:fldSimple")
    campo.set(qn("w:instr"), "PAGE")
    execucao = OxmlElement("w:r")
    texto = OxmlElement("w:t")
    texto.text = "1"
    execucao.append(texto)
    campo.append(execucao)
    paragrafo._p.append(campo)


def _rgb(hexadecimal: str | None) -> Any:
    from docx.shared import RGBColor

    return RGBColor.from_string((hexadecimal or "#000000").lstrip("#").upper())


def gerar_docx(layout: dict[str, Any], destino: Path) -> None:
    """Monta o `.docx` de template com as mesmas seções, rótulos e variáveis do HTML."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    tipografia = layout["tipografia"]
    margens = layout["pagina"]["margens_cm"]
    cores = layout["cores"]
    capa = layout["capa"]
    rosto = layout.get("folha_de_rosto")
    cabecalho = layout["cabecalho"]["logo"]
    rodape = layout["rodape"]
    fotos = layout["relatorio_fotografico"]
    legenda = fotos["legenda"]
    analise = layout["analise_por_sistema"]
    assinatura = layout.get("assinatura") or {}

    documento = Document()
    propriedades = documento.core_properties
    propriedades.author = "Garra Engenharia"
    propriedades.title = capa["titulo"]["texto"]
    propriedades.created = DATA_FIXA_DOCX
    propriedades.modified = DATA_FIXA_DOCX
    propriedades.last_modified_by = "build_vistoria_residencial_templates"
    propriedades.revision = 1

    estilo = documento.styles["Normal"]
    estilo.font.name = tipografia["familia"]
    estilo.font.size = Pt(tipografia["corpo_pt"])
    estilo.font.color.rgb = _rgb(cores["texto"])

    secao = documento.sections[0]
    secao.page_width = Pt(layout["pagina"]["largura_pt"])
    secao.page_height = Pt(layout["pagina"]["altura_pt"])
    secao.left_margin = Cm(margens["esquerda"])
    secao.right_margin = Cm(margens["direita"])
    secao.top_margin = Cm(margens["superior"])
    secao.bottom_margin = Cm(margens["inferior"])
    # Capa sem cabeçalho nem rodapé, como no original.
    secao.different_first_page_header_footer = True

    if cabecalho and LOGO_PNG.is_file():
        topo = secao.header.paragraphs[0]
        topo.alignment = WD_ALIGN_PARAGRAPH.RIGHT if cabecalho["alinhamento"] == "direita" else WD_ALIGN_PARAGRAPH.CENTER
        topo.add_run().add_picture(str(LOGO_PNG), width=Cm(_cm(cabecalho["largura_pt"])))

    pe = secao.footer.paragraphs[0]
    for indice, (papel, texto) in enumerate(zip(rodape["papeis"], rodape["linhas"], strict=True)):
        paragrafo = pe if indice == 0 else secao.footer.add_paragraph()
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        execucao = paragrafo.add_run(texto)
        execucao.font.size = Pt(rodape["fonte_pt"])
        if rodape["familia"]:
            execucao.font.name = rodape["familia"]
        if papel == "contato" and cores.get("link"):
            execucao.font.color.rgb = _rgb(cores["link"])
    numeracao = rodape.get("numeracao_pagina")
    if numeracao:
        paragrafo_numero = secao.footer.add_paragraph()
        paragrafo_numero.alignment = (
            WD_ALIGN_PARAGRAPH.RIGHT if numeracao["alinhamento"] == "direita" else WD_ALIGN_PARAGRAPH.CENTER
        )
        _campo_pagina(paragrafo_numero)

    def paragrafo_formatado(texto: str, tamanho: float, *, negrito: bool = False, centro: bool = False,
                            familia: str | None = None, cor: str | None = None, italico: bool = False) -> Any:
        paragrafo = documento.add_paragraph()
        if centro:
            paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        execucao = paragrafo.add_run(texto)
        execucao.bold = negrito
        execucao.italic = italico
        execucao.font.size = Pt(tamanho)
        if familia:
            execucao.font.name = familia
        if cor:
            execucao.font.color.rgb = _rgb(cor)
        return paragrafo

    def laco(expressao: str, corpo: str) -> None:
        documento.add_paragraph("{%p for " + expressao + " %}")
        documento.add_paragraph(corpo)
        documento.add_paragraph("{%p endfor %}")

    # Capa. O DOCX não tem a foto de fundo sangrada da capa: o texto usa a cor de
    # corpo, não a cor clara medida sobre a foto (que ficaria invisível no papel).
    secundarios = capa.get("corpos_secundarios_pt") or [tipografia["titulo_pt"]]
    if LOGO_PNG.is_file():
        logo = documento.add_paragraph()
        logo.alignment = WD_ALIGN_PARAGRAPH.RIGHT if (capa.get("logo") or {}).get("alinhamento") == "direita" else WD_ALIGN_PARAGRAPH.CENTER
        logo.add_run().add_picture(str(LOGO_PNG), width=Cm(_cm((capa.get("logo") or {}).get("largura_pt") or 216)))
    for linha in capa["titulo"].get("linhas") or [capa["titulo"]["texto"]]:
        paragrafo_formatado(linha, capa["titulo"]["fonte_pt"], negrito=True, centro=True, familia=capa["titulo"]["familia"])
    paragrafo_formatado("{{ imovel.unidade }}", secundarios[0], negrito=True, centro=True)
    paragrafo_formatado("{{ edificacao.nome }}", secundarios[0], negrito=True, centro=True)
    paragrafo_formatado(capa.get("rotulo_responsavel") or "RESP. TÉCNICO:", secundarios[-1], negrito=True)
    paragrafo_formatado("ENG. CIVIL {{ fiscal.nome|upper }}", secundarios[-1], negrito=True)
    paragrafo_formatado("{{ data_emissao|upper }}  CREA: {{ fiscal.crea }}", secundarios[-1], negrito=True)
    documento.add_page_break()

    if rosto:
        for linha in rosto["titulo"]["linhas"]:
            paragrafo_formatado(linha, rosto["titulo"]["fonte_pt"], negrito=True, centro=True)
        paragrafo_formatado("{{ imovel.unidade }}", rosto["identificacao"]["fonte_pt"], negrito=True, centro=True)
        paragrafo_formatado("{{ edificacao.nome }}", rosto["identificacao"]["fonte_pt"], negrito=True, centro=True)
        paragrafo_formatado(
            "{{ data_emissao }}", (rosto.get("data") or {}).get("fonte_pt", tipografia["titulo_pt"]), negrito=True, centro=True
        )
        documento.add_page_break()

    capitulos = _capitulos(layout)
    for posicao, capitulo in enumerate(capitulos):
        paragrafo_formatado(f"{capitulo['numero']} {capitulo['titulo']}", _fonte_do_nivel(layout, 1), negrito=True)
        laco(f"paragrafo in textos.{chave_secao(capitulo['numero'])}", "{{ paragrafo }}")
        for subsecao in capitulo["subsecoes"]:
            paragrafo_formatado(
                f"{subsecao['numero']} {subsecao['titulo']}", _fonte_do_nivel(layout, subsecao["nivel"]), negrito=True
            )
            laco(f"paragrafo in textos.{chave_secao(subsecao['numero'])}", "{{ paragrafo }}")

        if capitulo["tipo"] == "fotografico":
            documento.add_paragraph("{%p for foto in fotos %}")
            figura = documento.add_paragraph("{{ foto.imagem }}")
            figura.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragrafo_formatado(
                f"{legenda['rotulo']} {{{{ foto.numero }}}} {legenda['separador']} {{{{ foto.legenda }}}}. "
                f"Fonte: {{{{ foto.fonte or \"{legenda['fonte_padrao'] or 'Autor'}\" }}}}.",
                legenda["fonte_pt"],
                centro=True,
                familia=legenda["familia"],
                cor=legenda["cor"],
                italico=legenda["italico"],
            )
            documento.add_paragraph("{%p endfor %}")
        elif capitulo["tipo"] == "por_sistema":
            documento.add_paragraph("{%p for sistema in sistemas %}")
            paragrafo_formatado(
                f"{capitulo['numero']}{{{{ loop.index }}}}. {{{{ sistema.nome }}}}", _fonte_do_nivel(layout, 2), negrito=True
            )
            for subtitulo in analise["subtitulos"]:
                paragrafo_formatado(f"{analise['marcador'] or ''} {subtitulo['rotulo']}".strip(), analise["fonte_pt"], negrito=True)
                laco(f"item in sistema.{subtitulo['chave']}", ("• " if subtitulo["lista"] else "") + "{{ item }}")
            documento.add_paragraph("{%p endfor %}")

        if assinatura.get("secao") == capitulo["numero"]:
            alinhamento = WD_ALIGN_PARAGRAPH.RIGHT if assinatura.get("alinhamento") == "direita" else WD_ALIGN_PARAGRAPH.CENTER
            corpo_assinatura = assinatura.get("fonte_pt") or tipografia["corpo_pt"]
            for texto, negrito in (
                ("________________________________________", False),
                ("{{ fiscal.nome }}", bool(assinatura.get("nome_negrito", True))),
                ("Eng. Civil - CREA nº {{ fiscal.crea }}", False),
            ):
                paragrafo_formatado(texto, corpo_assinatura, negrito=negrito, familia=assinatura.get("familia")).alignment = alinhamento
            documento.add_paragraph("{%p for qualificacao in fiscal.qualificacoes %}")
            paragrafo_formatado("{{ qualificacao }}", corpo_assinatura, familia=assinatura.get("familia")).alignment = alinhamento
            documento.add_paragraph("{%p endfor %}")
            paragrafo_formatado(
                "{{ local_emissao }}, {{ data_emissao }}.", corpo_assinatura, familia=assinatura.get("familia")
            ).alignment = alinhamento

        if posicao + 1 < len(capitulos):
            documento.add_page_break()

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(destino)


# --------------------------------------------------------------------------- CLI


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
    parser = argparse.ArgumentParser(description="Gera os templates da Vistoria Residencial a partir do PDF original.")
    parser.add_argument("--original", type=Path, default=None, help="Caminho do PDF original do laudo.")
    argumentos = parser.parse_args(argv)

    try:
        layout = _carregar_layout(argumentos.original)
    except LayoutExtractionError as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    if argumentos.original is not None:
        LAYOUT_JSON.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"layout.json atualizado a partir do original informado (sha256 {layout['origem']['sha256'][:16]}…)")

    HTML_TEMPLATE.write_text(gerar_html(layout), encoding="utf-8")
    gerar_docx(layout, DOCX_TEMPLATE)
    print(f"gerados: {HTML_TEMPLATE.name}, {DOCX_TEMPLATE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
