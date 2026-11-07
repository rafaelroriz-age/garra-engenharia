"""Deriva os templates do RFIP (HTML/Jinja2 + DOCX) do mesmo `layout.json`.

Pipeline determinístico de ADR-13/DEC-25:

    01_output-context/<original>.xlsx           (~479 MB, fora do Git)
        -> app/scripts/rfip_layout_extractor.extrair_layout()   (read_only/streaming)
        -> 04_backend/templates/rfip/layout.json                (versionado)
        -> 04_backend/templates/rfip/rfip_template.html.j2      (WeasyPrint, ADR-01)
        -> 04_backend/templates/rfip/rfip_template.docx         (docxtpl, ADR-04)

Uso (um único comando gera os dois templates):

    python -m app.scripts.build_rfip_templates
    python -m app.scripts.build_rfip_templates --original "../01_output-context/<RFIP>.xlsx"

Sem `--original`, reutiliza o `layout.json` versionado (CI e máquinas sem o arquivo do
cliente). HTML e DOCX consomem a mesma especificação de ficha (`especificacao_ficha`),
então rótulos, campos, mesclagens e medidas não podem divergir entre os formatos.

Contexto esperado pelos templates (mesmo do LTIP): `sistemas[]` com `nome` e
`ocorrencias[]` (`seq_numero`, `situacao`, `gut_*`, `pontuacao_gut`, `classificacao`,
`tipo_anomalia`/`tipo_falha`, `grau_risco`, `subsistema`, `localizacao`, `descricao`,
`foto_data_uri` no HTML, `foto_docx` — InlineImage — no DOCX), `responsavel`
(`nome`, `titulo_profissional`, `crea`, `email`, `telefone`), `logo_data_uri` e
`incluir_resumo`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from html import escape
from pathlib import Path
from typing import Any

from app.scripts.rfip_layout_extractor import (
    LayoutExtractionError,
    extrair_layout,
    garantir_sem_dados_pessoais,
    slug,
)

TEMPLATES_RFIP_DIR = Path(__file__).resolve().parents[2] / "templates" / "rfip"
LAYOUT_JSON = TEMPLATES_RFIP_DIR / "layout.json"
HTML_TEMPLATE = TEMPLATES_RFIP_DIR / "rfip_template.html.j2"
DOCX_TEMPLATE = TEMPLATES_RFIP_DIR / "rfip_template.docx"
LOGO_PNG = TEMPLATES_RFIP_DIR.parent / "assets" / "logo-garra.png"

CABECALHO_GERADO = (
    "ARQUIVO GERADO — não editar à mão. "
    "Produzido por `python -m app.scripts.build_rfip_templates` a partir de "
    "templates/rfip/layout.json (ADR-13/DEC-25)."
)

#: Campo do original (slug do rótulo da coluna auxiliar) -> expressão do contexto.
#: Mesmos nomes do template do LTIP (BL-17), que também imprime a ficha fotográfica.
CAMPOS_CONTEXTO = {
    "situacao": "ocorrencia.situacao",
    "gravidade": "ocorrencia.gut_gravidade",
    "urgencia": "ocorrencia.gut_urgencia",
    "tendencia": "ocorrencia.gut_tendencia",
    "pontuacao": "ocorrencia.pontuacao_gut",
    "classificacao": "ocorrencia.classificacao",
    "tipo_de_anomalia": "(ocorrencia.tipo_anomalia or ocorrencia.tipo_falha)",
    "tipo_de_falha": "(ocorrencia.tipo_anomalia or ocorrencia.tipo_falha)",
    "tipo": "(ocorrencia.tipo_anomalia or ocorrencia.tipo_falha)",
    "grau_de_risco": "ocorrencia.grau_risco",
    "sistema": "sistema.nome",
    "subsistema": "ocorrencia.subsistema",
    "localizacao": "ocorrencia.localizacao",
    "observacoes_tecnicas": "ocorrencia.descricao",
}
#: Fontes do Office -> equivalentes métricos livres disponíveis no container do WeasyPrint.
#: Aspas simples: os nomes também vão em atributos `style="..."` inline.
FONTES_ALTERNATIVAS = {
    "Calibri": "'Carlito', sans-serif",
    "Cambria": "'Caladea', serif",
    "Times New Roman": "'Liberation Serif', 'Tinos', serif",
}
#: Estilo de borda do OOXML -> CSS / `w:val` + espessura em oitavos de ponto (DOCX).
BORDAS = {
    "hair": ("0.25pt solid", "single", 2),
    "thin": ("0.5pt solid", "single", 4),
    "medium": ("1pt solid", "single", 8),
    "thick": ("1.5pt solid", "single", 12),
    "dashed": ("0.5pt dashed", "dashed", 4),
    "dotted": ("0.5pt dotted", "dotted", 4),
    "double": ("1.5pt double", "double", 4),
}
LADOS = (("top", "top"), ("right", "right"), ("bottom", "bottom"), ("left", "left"))


# ----------------------------------------------------- especificação compartilhada


def _expressao(campo: str) -> str:
    return CAMPOS_CONTEXTO.get(campo, f'(ocorrencia.campos or {{}}).get("{campo}")')


def _valor(campo: str) -> str:
    """Tag Jinja do valor; vazio sai como "—" (DEC-33). Idêntica no HTML e no DOCX."""
    expressao = _expressao(campo)
    return "{{ " + f'{expressao} if {expressao} not in (none, "") else "—"' + " }}"


def _familia(nome: str | None, padrao: str) -> str:
    nome = nome or padrao
    return f"'{nome}', {FONTES_ALTERNATIVAS.get(nome, 'sans-serif')}"


def colunas_da_ficha(layout: dict[str, Any]) -> list[dict[str, Any]]:
    """Colunas impressas ocupadas pela ficha, na ordem da grade medida."""
    grade = [coluna["coluna"] for coluna in layout["grade"]["colunas"]]
    usadas: set[int] = set()
    for celula in layout["ficha"]["celulas"]:
        inicio = grade.index(celula["coluna"])
        usadas.update(range(inicio, inicio + celula["colunas"]))
    return [layout["grade"]["colunas"][i] for i in range(min(usadas), max(usadas) + 1)]


def _deslocamento_esquerdo_cm(layout: dict[str, Any]) -> float:
    primeira = colunas_da_ficha(layout)[0]["coluna"]
    deslocamento = 0.0
    for coluna in layout["grade"]["colunas"]:
        if coluna["coluna"] == primeira:
            break
        deslocamento += coluna["largura_cm"]
    return round(deslocamento, 2)


def especificacao_ficha(layout: dict[str, Any]) -> list[dict[str, Any]]:
    """Células da ficha já resolvidas para template: posição, extensão, conteúdo e estilo.

    É a única fonte dos dois geradores — o teste de paridade compara a saída de
    ambos contra esta lista.
    """
    ficha = layout["ficha"]
    grade = [coluna["coluna"] for coluna in colunas_da_ficha(layout)]
    legenda = ficha["legenda"]
    especificacao = []
    for celula in ficha["celulas"]:
        papel = celula["papel"]
        if papel == "titulo_foto":
            conteudo = f'{legenda["prefixo"]} ' + "{{ " + f'"%0{legenda["digitos"]}d"|format(ocorrencia.seq_numero)' + " }}"
        elif papel == "valor":
            conteudo = _valor(celula["campo"])
        elif papel == "rotulo" and celula.get("sufixo_campo"):
            expressao = _expressao(celula["sufixo_campo"])
            conteudo = celula["texto"] + " {{ (" + expressao + ' or "")|upper }}'
        elif papel == "rotulo":
            conteudo = celula["texto"]
        else:
            conteudo = ""  # foto (tratada à parte), vazio e texto descartado do exemplar
        especificacao.append(
            {
                "linha": celula["linha"],
                "coluna": grade.index(celula["coluna"]),
                "linhas": celula["linhas"],
                "colunas": celula["colunas"],
                "papel": papel,
                "conteudo": conteudo,
                "estilo": celula.get("estilo") or {},
            }
        )
    return especificacao


def tamanho_foto_cm(layout: dict[str, Any]) -> tuple[float, float] | None:
    foto = layout["ficha"].get("foto") or {}
    if not foto.get("largura_cm") or not foto.get("altura_cm"):
        return None
    escala = layout["grade"]["escala_impressao"]
    return round(foto["largura_cm"] * escala, 2), round(foto["altura_cm"] * escala, 2)


def tamanho_logo_cm(layout: dict[str, Any]) -> tuple[float, float] | None:
    """Logo do cabeçalho limitada à margem superior (no Excel a margem de cabeçalho é 0)."""
    for linha in layout["cabecalho"]["secoes"].get("direita", []):
        imagem = linha.get("imagem")
        if imagem:
            largura, altura = imagem["largura_cm"], imagem["altura_cm"]
            limite = layout["pagina"]["margens_cm"]["superior"] - 0.2
            if altura > limite > 0:
                largura, altura = largura * limite / altura, limite
            return round(largura, 2), round(altura, 2)
    return None


def alturas_linhas_pt(layout: dict[str, Any]) -> list[float]:
    escala = layout["grade"]["escala_impressao"]
    return [round(altura * escala, 2) for altura in layout["ficha"]["alturas_pt"]]


def _linhas_rodape(layout: dict[str, Any], secao: str) -> list[list[dict[str, Any]]]:
    return [linha["trechos"] for linha in layout["rodape"]["secoes"].get(secao, [])]


# ------------------------------------------------------------------------- HTML


def _css_celula(estilo: dict[str, Any], padrao_fonte: str) -> str:
    regras = []
    if estilo.get("fonte"):
        regras.append(f"font-family: {_familia(estilo['fonte'], padrao_fonte)}")
    if estilo.get("corpo_pt"):
        regras.append(f"font-size: {estilo['corpo_pt']}pt")
    if estilo.get("negrito"):
        regras.append("font-weight: bold")
    if estilo.get("italico"):
        regras.append("font-style: italic")
    if estilo.get("cor"):
        regras.append(f"color: {estilo['cor']}")
    if estilo.get("fundo"):
        regras.append(f"background: {estilo['fundo']}")
    if estilo.get("alinhamento_h") in ("left", "center", "right", "justify"):
        regras.append(f"text-align: {estilo['alinhamento_h']}")
    regras.append(f"vertical-align: {'middle' if estilo.get('alinhamento_v') == 'center' else estilo.get('alinhamento_v') or 'bottom'}")
    for lado, chave in LADOS:
        borda = (estilo.get("bordas") or {}).get(chave)
        if borda:
            regras.append(f"border-{lado}: {BORDAS.get(borda, BORDAS['thin'])[0]} #000000")
    return "; ".join(regras)


def _linhas_html_rodape(layout: dict[str, Any], secao: str) -> str:
    cor_texto = layout["cores"]["texto"]
    linhas = []
    for trechos in _linhas_rodape(layout, secao):
        partes = []
        for trecho in trechos:
            if not trecho.get("placeholder"):
                continue
            estilo = [f"color: {trecho.get('cor') or cor_texto}"]
            if trecho.get("negrito"):
                estilo.append("font-weight: bold")
            partes.append(f'<span style="{"; ".join(estilo)}">{trecho["placeholder"]}</span>')
        if partes:
            linhas.append("".join(partes))
    return "<br>".join(linhas)


def gerar_html(layout: dict[str, Any]) -> str:
    pagina = layout["pagina"]
    margens = pagina["margens_cm"]
    tipografia = layout["tipografia"]
    fonte_padrao = tipografia["padrao_planilha"]
    titulo_sistema = layout["titulo_sistema"] or {}
    estilo_titulo = titulo_sistema.get("estilo") or {}
    colunas = colunas_da_ficha(layout)
    alturas = alturas_linhas_pt(layout)
    foto = tamanho_foto_cm(layout)
    logo = tamanho_logo_cm(layout)
    especificacao = especificacao_ficha(layout)
    capitulo = (titulo_sistema.get("numeracao") or {}).get("capitulo")

    # Grade: emite cada linha pulando as posições cobertas por rowspan/colspan.
    inicio = {(c["linha"], c["coluna"]): c for c in especificacao}
    cobertas: set[tuple[int, int]] = set()
    linhas_html = []
    for indice_linha, altura in enumerate(alturas):
        celulas_html = []
        for indice_coluna in range(len(colunas)):
            if (indice_linha, indice_coluna) in cobertas:
                continue
            celula = inicio.get((indice_linha, indice_coluna))
            if celula is None:
                celulas_html.append("<td></td>")
                continue
            for lin in range(indice_linha, indice_linha + celula["linhas"]):
                for col in range(indice_coluna, indice_coluna + celula["colunas"]):
                    cobertas.add((lin, col))
            atributos = ""
            if celula["linhas"] > 1:
                atributos += f' rowspan="{celula["linhas"]}"'
            if celula["colunas"] > 1:
                atributos += f' colspan="{celula["colunas"]}"'
            if celula["papel"] == "foto":
                dimensao = f"width: {foto[0]}cm; height: {foto[1]}cm; " if foto else "max-width: 100%; "
                conteudo = (
                    "{% if ocorrencia.foto_data_uri %}"
                    f'<img src="{{{{ ocorrencia.foto_data_uri }}}}" style="{dimensao}object-fit: contain" '
                    f'alt="{escape(layout["ficha"]["legenda"]["prefixo"])} {{{{ ocorrencia.seq_numero }}}}">'
                    "{% endif %}"
                )
            else:
                conteudo = escape(celula["conteudo"], quote=False)
            celulas_html.append(
                f'<td data-papel="{celula["papel"]}"{atributos} style="{_css_celula(celula["estilo"], tipografia["familia"])}">{conteudo}</td>'
            )
        linhas_html.append(f'        <tr style="height: {altura}pt">' + "".join(celulas_html) + "</tr>")

    colgroup = "".join(f'<col style="width: {coluna["largura_cm"]}cm">' for coluna in colunas)
    largura_ficha = round(sum(coluna["largura_cm"] for coluna in colunas), 2)
    rodape_centro = _linhas_html_rodape(layout, "centro")
    numero_pagina = any(
        trecho.get("papel") == "numero_pagina" for trechos in _linhas_rodape(layout, "direita") for trecho in trechos
    )
    fonte_rodape = f"font-family: {_familia(fonte_padrao['familia'], tipografia['familia'])}; font-size: {fonte_padrao['corpo_pt']}pt"

    resumo_html = ""
    resumo = layout.get("resumo")
    if resumo:
        margens_resumo = (resumo.get("pagina") or pagina)["margens_cm"]
        total = sum(c.get("largura_caracteres") or 0 for c in resumo["cabecalho"]) or 1
        cabecalho = "".join(
            f'<th style="width: {round(100 * (c.get("largura_caracteres") or 0) / total, 2)}%; {_css_celula(c["estilo"], tipografia["familia"])}">{escape(c["rotulo"])}</th>'
            for c in resumo["cabecalho"]
        )
        estilo_corpo = _css_celula(resumo.get("estilo_corpo") or {}, tipografia["familia"])
        celulas_resumo = "".join(f'<td style="{estilo_corpo}">{escape(conteudo, quote=False)}</td>' for conteudo in conteudo_resumo(layout))
        resumo_html = f"""
  {{% if incluir_resumo %}}
  <section class="resumo">
    <table class="resumo">
      <thead><tr>{cabecalho}</tr></thead>
      <tbody>
        {{% for sistema in sistemas %}}{{% for ocorrencia in sistema.ocorrencias %}}
        <tr>{celulas_resumo}</tr>
        {{% endfor %}}{{% endfor %}}
      </tbody>
    </table>
  </section>
  {{% endif %}}"""
        pagina_resumo = (
            f"  @page resumo {{ margin: {margens_resumo['superior']}cm {margens_resumo['direita']}cm "
            f"{margens_resumo['inferior']}cm {margens_resumo['esquerda']}cm; }}\n"
            "  section.resumo { page: resumo; break-before: page; }\n"
            "  table.resumo { width: 100%; border-collapse: collapse; table-layout: fixed; }\n"
            "  table.resumo td, table.resumo th { padding: 1pt 2pt; overflow-wrap: anywhere; }\n"
        )
    else:
        pagina_resumo = ""

    titulo_h2 = (
        f"{capitulo}.{{{{ loop.index }}}}. {{{{ sistema.nome }}}}" if capitulo is not None else "{{ sistema.nome }}"
    )
    logo_css = f"width: {logo[0]}cm; height: {logo[1]}cm;" if logo else "height: 2cm;"
    origem = layout["origem"]

    return f"""<!DOCTYPE html>
{{#
  {CABECALHO_GERADO}

  Layout derivado do original sha256 {origem['sha256'][:16]}… (aba fotográfica {origem['aba_fotografica']!r},
  {origem['linhas_lidas']} linhas lidas). Ficha: {layout['ficha']['linhas_por_ficha']} linhas,
  {layout['ficha']['fichas_por_pagina']} por página no original.
#}}
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório Fotográfico de Inspeção Predial</title>
<style>
  @page {{
    size: {pagina['tamanho']} {pagina['orientacao']};
    margin: {margens['superior']}cm {margens['direita']}cm {margens['inferior']}cm {margens['esquerda']}cm;
    @top-right {{ content: element(logo); vertical-align: top; }}
    @bottom-center {{ content: element(rodape); vertical-align: bottom; }}
    {"@bottom-right { content: counter(page); vertical-align: bottom; " + fonte_rodape + "; }" if numero_pagina else ""}
  }}
{pagina_resumo}  body {{
    font-family: {_familia(tipografia['familia'], 'Calibri')};
    font-size: {tipografia['corpo_pt']}pt;
    color: {layout['cores']['texto']};
    margin: 0;
  }}
  .logo {{ position: running(logo); }}
  .logo img {{ {logo_css} object-fit: contain; }}
  .rodape {{ position: running(rodape); text-align: center; {fonte_rodape}; }}
  .conteudo {{ margin-left: {_deslocamento_esquerdo_cm(layout)}cm; }}
  h2.sistema {{
    font-family: {_familia(estilo_titulo.get('fonte'), tipografia['familia'])};
    font-size: {estilo_titulo.get('corpo_pt') or tipografia['corpo_pt']}pt;
    font-weight: {'bold' if estilo_titulo.get('negrito', True) else 'normal'};
    text-align: {estilo_titulo.get('alinhamento_h') or 'left'};
    height: {titulo_sistema.get('altura_pt', 14.25)}pt;
    margin: 0 0 {titulo_sistema.get('espaco_apos_pt', 0)}pt 0;
    break-after: avoid;
  }}
  table.ficha {{ width: {largura_ficha}cm; border-collapse: collapse; table-layout: fixed; break-inside: avoid; }}
  table.ficha td {{ padding: 0 2pt; overflow: hidden; white-space: pre-line; }}
</style>
</head>
<body>
  <div class="logo">{{% if logo_data_uri %}}<img src="{{{{ logo_data_uri }}}}" alt="Garra Engenharia">{{% endif %}}</div>
  <div class="rodape">{rodape_centro}</div>

  <main class="conteudo">
  {{% for sistema in sistemas %}}
  <section class="sistema">
    <h2 class="sistema">{titulo_h2}</h2>
    {{% for ocorrencia in sistema.ocorrencias %}}
    <table class="ficha">
      <colgroup>{colgroup}</colgroup>
      <tbody>
{chr(10).join(linhas_html)}
      </tbody>
    </table>
    {{% endfor %}}
  </section>
  {{% endfor %}}
  </main>
{resumo_html}
</body>
</html>
"""


def conteudo_resumo(layout: dict[str, Any]) -> list[str]:
    """Uma tag por coluna do quadro-resumo; a coluna "Imagem" repete a legenda da foto."""
    legenda = layout["ficha"]["legenda"]
    conteudos = []
    for coluna in (layout.get("resumo") or {}).get("cabecalho", []):
        chave = slug(coluna["rotulo"])
        if chave == "imagem":
            conteudos.append(f'{legenda["prefixo"]} ' + "{{ " + f'"%0{legenda["digitos"]}d"|format(ocorrencia.seq_numero)' + " }}")
        else:
            conteudos.append(_valor(chave))
    return conteudos


# ------------------------------------------------------------------------- DOCX


def _sombrear(celula: Any, cor: str) -> None:
    from docx.oxml.ns import qn
    from docx.oxml.shared import OxmlElement

    sombreamento = OxmlElement("w:shd")
    sombreamento.set(qn("w:val"), "clear")
    sombreamento.set(qn("w:color"), "auto")
    sombreamento.set(qn("w:fill"), cor.lstrip("#"))
    celula._tc.get_or_add_tcPr().append(sombreamento)


def _bordas_docx(celula: Any, bordas: dict[str, str]) -> None:
    from docx.oxml.ns import qn
    from docx.oxml.shared import OxmlElement

    propriedades = celula._tc.get_or_add_tcPr()
    elemento = OxmlElement("w:tcBorders")
    for lado, chave in LADOS:
        borda = bordas.get(chave)
        if not borda:
            continue
        _css, valor, espessura = BORDAS.get(borda, BORDAS["thin"])
        filho = OxmlElement(f"w:{lado}")
        filho.set(qn("w:val"), valor)
        filho.set(qn("w:sz"), str(espessura))
        filho.set(qn("w:space"), "0")
        filho.set(qn("w:color"), "000000")
        elemento.append(filho)
    propriedades.append(elemento)


def _campo_pagina(paragrafo: Any) -> None:
    from docx.oxml.ns import qn
    from docx.oxml.shared import OxmlElement

    campo = OxmlElement("w:fldSimple")
    campo.set(qn("w:instr"), "PAGE")
    execucao = OxmlElement("w:r")
    texto = OxmlElement("w:t")
    texto.text = "1"
    execucao.append(texto)
    campo.append(execucao)
    paragrafo._p.append(campo)


def _rgb(cor: str | None) -> Any:
    from docx.shared import RGBColor

    return RGBColor.from_string((cor or "#000000").lstrip("#"))


def _formatar_execucao(execucao: Any, estilo: dict[str, Any], padrao_fonte: str) -> None:
    from docx.shared import Pt

    execucao.font.name = estilo.get("fonte") or padrao_fonte
    if estilo.get("corpo_pt"):
        execucao.font.size = Pt(estilo["corpo_pt"])
    execucao.bold = bool(estilo.get("negrito"))
    execucao.italic = bool(estilo.get("italico"))
    if estilo.get("cor"):
        execucao.font.color.rgb = _rgb(estilo["cor"])


def _paragrafo_de_controle(documento: Any, tag: str) -> None:
    """Parágrafo que só carrega `{%p ... %}` — o docxtpl o remove na renderização."""
    documento.add_paragraph(tag)


def gerar_docx(layout: dict[str, Any], destino: Path) -> None:
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml.shared import OxmlElement
    from docx.shared import Cm, Pt

    pagina = layout["pagina"]
    margens = pagina["margens_cm"]
    tipografia = layout["tipografia"]
    fonte_padrao = tipografia["padrao_planilha"]
    titulo_sistema = layout["titulo_sistema"] or {}
    estilo_titulo = titulo_sistema.get("estilo") or {}
    colunas = colunas_da_ficha(layout)
    alturas = alturas_linhas_pt(layout)
    logo = tamanho_logo_cm(layout)
    capitulo = (titulo_sistema.get("numeracao") or {}).get("capitulo")
    alinhamentos_h = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER, "right": WD_ALIGN_PARAGRAPH.RIGHT, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY}
    alinhamentos_v = {"top": WD_CELL_VERTICAL_ALIGNMENT.TOP, "center": WD_CELL_VERTICAL_ALIGNMENT.CENTER, "bottom": WD_CELL_VERTICAL_ALIGNMENT.BOTTOM}

    documento = Document()
    normal = documento.styles["Normal"]
    normal.font.name = tipografia["familia"]
    normal.font.size = Pt(tipografia["corpo_pt"])
    normal.paragraph_format.space_after = Pt(0)

    secao = documento.sections[0]
    secao.orientation = WD_ORIENT.LANDSCAPE if pagina["orientacao"] == "landscape" else WD_ORIENT.PORTRAIT
    # python-docx nasce em Carta; o original é A4.
    largura, altura = (Cm(21.0), Cm(29.7)) if pagina["tamanho"] == "A4" else (secao.page_width, secao.page_height)
    secao.page_width, secao.page_height = (altura, largura) if pagina["orientacao"] == "landscape" else (largura, altura)
    secao.left_margin = Cm(margens["esquerda"])
    secao.right_margin = Cm(margens["direita"])
    secao.top_margin = Cm(margens["superior"])
    secao.bottom_margin = Cm(margens["inferior"])
    secao.header_distance = Cm(margens["cabecalho"])
    secao.footer_distance = Cm(margens["rodape"])

    # Cabeçalho: logo à direita (`&R&G` no original).
    cabecalho = secao.header.paragraphs[0]
    cabecalho.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if logo and LOGO_PNG.is_file():
        cabecalho.add_run().add_picture(str(LOGO_PNG), width=Cm(logo[0]), height=Cm(logo[1]))

    # Rodapé: seções esquerda/centro/direita do Excel viram uma tabela de 3 colunas.
    util = Cm(21.0 - margens["esquerda"] - margens["direita"])
    tabela_rodape = secao.footer.add_table(rows=1, cols=3, width=util)
    for indice, chave in enumerate(("esquerda", "centro", "direita")):
        celula = tabela_rodape.cell(0, indice)
        celula.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.BOTTOM
        paragrafo = celula.paragraphs[0]
        paragrafo.alignment = (WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT)[indice]
        for numero, trechos in enumerate(_linhas_rodape(layout, chave)):
            if numero:
                paragrafo = celula.add_paragraph()
                paragrafo.alignment = (WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT)[indice]
            for trecho in trechos:
                if trecho.get("papel") == "numero_pagina":
                    _campo_pagina(paragrafo)
                    continue
                if not trecho.get("placeholder"):
                    continue
                execucao = paragrafo.add_run(trecho["placeholder"])
                _formatar_execucao(
                    execucao,
                    {"fonte": fonte_padrao["familia"], "corpo_pt": fonte_padrao["corpo_pt"], "negrito": trecho.get("negrito"), "cor": trecho.get("cor") or layout["cores"]["texto"]},
                    tipografia["familia"],
                )

    deslocamento = Cm(_deslocamento_esquerdo_cm(layout))

    _paragrafo_de_controle(documento, "{%p for sistema in sistemas %}")
    paragrafo_titulo = documento.add_paragraph()
    paragrafo_titulo.paragraph_format.left_indent = deslocamento
    paragrafo_titulo.paragraph_format.space_after = Pt(titulo_sistema.get("espaco_apos_pt", 0))
    paragrafo_titulo.paragraph_format.keep_with_next = True
    paragrafo_titulo.alignment = alinhamentos_h.get(estilo_titulo.get("alinhamento_h") or "left")
    execucao = paragrafo_titulo.add_run(
        f"{capitulo}.{{{{ loop.index }}}}. {{{{ sistema.nome }}}}" if capitulo is not None else "{{ sistema.nome }}"
    )
    _formatar_execucao(execucao, {**estilo_titulo, "negrito": estilo_titulo.get("negrito", True)}, tipografia["familia"])

    _paragrafo_de_controle(documento, "{%p for ocorrencia in sistema.ocorrencias %}")
    tabela = documento.add_table(rows=len(alturas), cols=len(colunas))
    tabela.alignment = WD_TABLE_ALIGNMENT.LEFT
    tabela.autofit = False
    propriedades = tabela._tbl.tblPr
    recuo = OxmlElement("w:tblInd")
    recuo.set(qn("w:w"), str(deslocamento.twips))
    recuo.set(qn("w:type"), "dxa")
    propriedades.append(recuo)
    layout_fixo = OxmlElement("w:tblLayout")
    layout_fixo.set(qn("w:type"), "fixed")
    propriedades.append(layout_fixo)
    for indice, coluna in enumerate(colunas):
        tabela.columns[indice].width = Cm(coluna["largura_cm"])
        for linha in tabela.rows:
            linha.cells[indice].width = Cm(coluna["largura_cm"])
    for indice, linha in enumerate(tabela.rows):
        linha.height = Pt(alturas[indice])
        linha.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
        sem_quebra = OxmlElement("w:cantSplit")
        linha._tr.get_or_add_trPr().append(sem_quebra)

    for celula_spec in especificacao_ficha(layout):
        celula = tabela.cell(celula_spec["linha"], celula_spec["coluna"])
        fim = tabela.cell(celula_spec["linha"] + celula_spec["linhas"] - 1, celula_spec["coluna"] + celula_spec["colunas"] - 1)
        if fim is not celula and (celula_spec["linhas"] > 1 or celula_spec["colunas"] > 1):
            celula = celula.merge(fim)
        estilo = celula_spec["estilo"]
        if estilo.get("fundo"):
            _sombrear(celula, estilo["fundo"])
        if estilo.get("bordas"):
            _bordas_docx(celula, estilo["bordas"])
        celula.vertical_alignment = alinhamentos_v.get(estilo.get("alinhamento_v") or "bottom", WD_CELL_VERTICAL_ALIGNMENT.BOTTOM)
        paragrafo = celula.paragraphs[0]
        paragrafo.alignment = alinhamentos_h.get(estilo.get("alinhamento_h") or "left", WD_ALIGN_PARAGRAPH.LEFT)
        if celula_spec["papel"] == "foto":
            # InlineImage do docxtpl montada pelo pipeline no tamanho medido da foto.
            paragrafo.add_run("{{ ocorrencia.foto_docx }}")
            continue
        if celula_spec["conteudo"]:
            _formatar_execucao(paragrafo.add_run(celula_spec["conteudo"]), estilo, tipografia["familia"])
    _paragrafo_de_controle(documento, "{%p endfor %}")
    _paragrafo_de_controle(documento, "{%p endfor %}")

    resumo = layout.get("resumo")
    if resumo:
        _paragrafo_de_controle(documento, "{%p if incluir_resumo %}")
        documento.add_page_break()
        colunas_resumo = resumo["cabecalho"]
        tabela_resumo = documento.add_table(rows=6, cols=len(colunas_resumo))
        total = sum(c.get("largura_caracteres") or 0 for c in colunas_resumo) or 1
        for indice, coluna in enumerate(colunas_resumo):
            largura_coluna = util * (coluna.get("largura_caracteres") or 0) / total
            for linha in tabela_resumo.rows:
                linha.cells[indice].width = largura_coluna
            celula = tabela_resumo.cell(0, indice)
            if coluna["estilo"].get("fundo"):
                _sombrear(celula, coluna["estilo"]["fundo"])
            _formatar_execucao(celula.paragraphs[0].add_run(coluna["rotulo"]), coluna["estilo"], tipografia["familia"])
        # `{%tr %}` remove a linha em que aparece: abertura e fechamento em linhas próprias.
        tabela_resumo.cell(1, 0).text = "{%tr for sistema in sistemas %}"
        tabela_resumo.cell(2, 0).text = "{%tr for ocorrencia in sistema.ocorrencias %}"
        for indice, conteudo in enumerate(conteudo_resumo(layout)):
            _formatar_execucao(tabela_resumo.cell(3, indice).paragraphs[0].add_run(conteudo), resumo.get("estilo_corpo") or {}, tipografia["familia"])
        tabela_resumo.cell(4, 0).text = "{%tr endfor %}"
        tabela_resumo.cell(5, 0).text = "{%tr endfor %}"
        _paragrafo_de_controle(documento, "{%p endif %}")

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.core_properties.title = "Relatório Fotográfico de Inspeção Predial"
    documento.core_properties.comments = CABECALHO_GERADO
    documento.save(str(destino))


# -------------------------------------------------------------------------- CLI


def gravar_layout(layout: dict[str, Any], destino: Path = LAYOUT_JSON) -> None:
    """Grava o layout.json de forma determinística (DEC-35 B: sem carimbo de data)."""
    garantir_sem_dados_pessoais(layout)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def gerar_templates(layout: dict[str, Any], pasta: Path = TEMPLATES_RFIP_DIR) -> tuple[Path, Path]:
    html = pasta / HTML_TEMPLATE.name
    docx = pasta / DOCX_TEMPLATE.name
    pasta.mkdir(parents=True, exist_ok=True)
    html.write_text(gerar_html(layout), encoding="utf-8")
    gerar_docx(layout, docx)
    return html, docx


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--original", type=Path, help="Caminho do .xlsx original do RFIP (01_output-context/).")
    parser.add_argument("--max-linhas", type=int, default=None, help="Linhas lidas da aba fotográfica (padrão do extrator).")
    parser.add_argument("--somente-layout", action="store_true", help="Extrai o layout.json sem gerar os templates.")
    argumentos = parser.parse_args(argv)

    if argumentos.original:
        tracemalloc.start()
        inicio = time.perf_counter()
        try:
            opcoes = {"max_linhas": argumentos.max_linhas} if argumentos.max_linhas else {}
            layout = extrair_layout(argumentos.original, **opcoes)
        except LayoutExtractionError as erro:
            print(f"ERRO: {erro}", file=sys.stderr)
            return 1
        finally:
            pico = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
        print(f"extração: {time.perf_counter() - inicio:.2f} s, pico de memória Python {pico / 1e6:.1f} MB (tracemalloc)")
        gravar_layout(layout)
        print(f"layout.json escrito em {LAYOUT_JSON}")
    else:
        if not LAYOUT_JSON.is_file():
            print(
                f"ERRO: {LAYOUT_JSON} não existe. Rode uma vez com --original apontando para o arquivo do cliente.",
                file=sys.stderr,
            )
            return 1
        layout = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))

    if argumentos.somente_layout:
        return 0

    html, docx = gerar_templates(layout)
    print(f"template HTML escrito em {html}")
    print(f"template DOCX escrito em {docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
