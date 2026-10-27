"""Deriva os templates do RFO (HTML/Jinja2 + DOCX) a partir do original do cliente.

Pipeline determinístico de ADR-13/DEC-25:

    01_output-context/<original>.xlsm
        -> app/scripts/rfo_layout_extractor.extrair_layout()
        -> 04_backend/templates/rfo/layout.json            (versionado)
        -> 04_backend/templates/rfo/rfo_template.html.j2   (WeasyPrint, ADR-01)
        -> 04_backend/templates/rfo/rfo_template.docx      (docxtpl, ADR-04)

Uso:

    python -m app.scripts.build_rfo_templates \
        --original "../01_output-context/Relatório de Fiscalização 1.xlsm"

Sem `--original`, reutiliza o `layout.json` já versionado (permite regerar os
templates em máquinas/CI que não têm o arquivo original do cliente).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.rfo_layout_extractor import LayoutExtractionError, extrair_layout

TEMPLATES_RFO_DIR = Path(__file__).resolve().parents[2] / "templates" / "rfo"
LAYOUT_JSON = TEMPLATES_RFO_DIR / "layout.json"
HTML_TEMPLATE = TEMPLATES_RFO_DIR / "rfo_template.html.j2"
DOCX_TEMPLATE = TEMPLATES_RFO_DIR / "rfo_template.docx"
# Marca com fundo transparente (RN-07/B-02) gerada por
# `python -m app.scripts.build_brand_assets`; o DOCX não aceita SVG.
LOGO_PNG = TEMPLATES_RFO_DIR.parent / "assets" / "logo-garra.png"

CABECALHO_GERADO = (
    "ARQUIVO GERADO — não editar à mão. "
    "Produzido por `python -m app.scripts.build_rfo_templates` a partir de "
    "templates/rfo/layout.json (ADR-13/DEC-25)."
)


def _titulos_de_secao(layout: dict[str, Any], parte: str) -> list[str]:
    return [secao["titulo"] for secao in layout[parte]["secoes"]]


def _secao(layout: dict[str, Any], parte: str, fragmento: str) -> dict[str, Any] | None:
    """Localiza uma seção pelo início do título, tolerando acentuação do original."""
    alvo = fragmento.casefold()
    for secao in layout[parte]["secoes"]:
        if secao["titulo"].casefold().startswith(alvo):
            return secao
    return None


def gerar_html(layout: dict[str, Any]) -> str:
    """Monta o `.html.j2` respeitando margens, fonte e cores medidas no original."""
    pagina = layout["pagina"]
    margens = pagina["margens_cm"]
    tipografia = layout["tipografia"]
    cores = layout["cores"]
    grade = layout["visita"]["registro_fotografico"]
    fotos_por_linha = grade.get("fotos_por_linha") or 2
    largura_foto = round(100 / fotos_por_linha - 2, 2)
    assinaturas = layout["visita"]["assinaturas"] or [
        "RESPONSÁVEL TÉCNICO / FISCALIZAÇÃO",
        "CONTRATADA",
        "CONTRATANTE",
    ]
    titulo_marca = (layout["cabecalho"]["titulo"] or {}).get("texto") or "Relatório de Fiscalização"
    endereco = next(
        (linha for linha in layout["cabecalho"]["linhas_texto"] if "Qd." in linha or "Rua" in linha),
        "",
    )

    linhas_assinatura = "\n".join(
        f'      <div class="assinatura"><span class="linha"></span>{nome}</div>' for nome in assinaturas
    )

    return f"""<!DOCTYPE html>
{{#
  {CABECALHO_GERADO}

  Layout derivado de: {layout['origem']['arquivo']} (sha256 {layout['origem']['sha256'][:16]}…)
  Abas usadas: capa={layout['origem']['aba_capa']!r}, visita modelo={layout['visita']['aba_modelo']!r}
#}}
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>{titulo_marca} — {{{{ contrato.numero }}}}</title>
<style>
  @page {{
    size: {pagina['tamanho']} {pagina['orientacao']};
    margin: {margens['superior']}cm {margens['direita']}cm {margens['inferior']}cm {margens['esquerda']}cm;
    @bottom-right {{
      content: "Folha nº " counter(page) " de " counter(pages);
      font-family: {tipografia['familia']}, sans-serif;
      font-size: 8pt;
    }}
  }}
  body {{
    font-family: {tipografia['familia']}, "DejaVu Sans", sans-serif;
    font-size: {tipografia['corpo_pt']}pt;
    color: {cores['texto']};
    margin: 0;
  }}
  .marca {{ display: flex; align-items: center; gap: 0.4cm; border-bottom: 1pt solid {cores['texto']}; padding-bottom: 0.2cm; }}
  .marca img {{ height: 2.2cm; }}
  .marca .titulo {{ font-size: 20pt; font-weight: bold; flex: 1; }}
  .marca .endereco {{ font-size: 8pt; text-align: right; max-width: 6cm; }}
  h2.secao {{
    background: {cores['cabecalho_secao_fundo']};
    font-size: {tipografia['corpo_pt']}pt;
    font-weight: bold;
    text-transform: uppercase;
    margin: 0.35cm 0 0.15cm 0;
    padding: 2pt 4pt;
  }}
  table.campos {{ width: 100%; border-collapse: collapse; }}
  table.campos td {{ border-bottom: 0.5pt solid #999; padding: 2pt 4pt; vertical-align: top; }}
  table.campos td.rotulo {{ font-weight: bold; white-space: nowrap; width: 1%; }}
  table.equipe {{ width: 60%; border-collapse: collapse; }}
  table.equipe th, table.equipe td {{ border: 0.5pt solid #999; padding: 2pt 4pt; text-align: left; }}
  table.equipe th {{ background: {cores['cabecalho_secao_fundo']}; }}
  ul.itens {{ margin: 0; padding-left: 0.6cm; }}
  ul.itens li {{ text-align: justify; }}
  .fotos {{ display: flex; flex-wrap: wrap; gap: 0.3cm; }}
  .foto {{ width: {largura_foto}%; }}
  .foto img {{ width: 100%; border: 0.5pt solid #999; }}
  .foto .legenda {{ font-size: {tipografia['corpo_pt']}pt; font-weight: bold; text-align: center; border-bottom: 0.5pt solid #999; }}
  .foto .descricao {{ font-size: 8pt; text-align: justify; }}
  .assinaturas {{ display: flex; justify-content: space-between; margin-top: 1.2cm; }}
  .assinatura {{ width: 30%; text-align: center; font-size: 8pt; }}
  .assinatura .linha {{ display: block; border-top: 0.5pt solid {cores['texto']}; margin-bottom: 2pt; }}
  .visita {{ page-break-before: always; }}
</style>
</head>
<body>
  {{% macro marca() %}}
  <header class="marca">
    {{% if logo_data_uri %}}<img src="{{{{ logo_data_uri }}}}" alt="Garra Engenharia">{{% endif %}}
    <div class="titulo">{titulo_marca}</div>
    <div class="endereco">{endereco}</div>
  </header>
  {{% endmacro %}}

  <section class="capa">
    {{{{ marca() }}}}

    <h2 class="secao">{(_secao(layout, 'capa', 'INFORMA') or {'titulo': 'Informações da Edificação'})['titulo']}</h2>
    <table class="campos">
      <tr><td class="rotulo">Local:</td><td>{{{{ edificacao.nome }}}}</td></tr>
      <tr><td class="rotulo">Endereço:</td><td>{{{{ edificacao.endereco }}}}</td></tr>
      <tr><td class="rotulo">Finalidade:</td><td>{{{{ edificacao.tipologia or "—" }}}}</td></tr>
    </table>

    <h2 class="secao">Informações Técnicas da Fiscalização</h2>
    <table class="campos">
      <tr><td class="rotulo">Contrato:</td><td>{{{{ contrato.numero }}}}</td></tr>
      <tr><td class="rotulo">Fiscal:</td><td>{{{{ fiscal.nome }}}}</td></tr>
      <tr><td class="rotulo">Nº CREA:</td><td>{{{{ fiscal.crea }}}}</td></tr>
      <tr><td class="rotulo">E-mail:</td><td>{{{{ fiscal.email or "—" }}}}</td></tr>
      <tr><td class="rotulo">ART de Fiscalização:</td><td>{{{{ contrato.art_fiscalizacao }}}}</td></tr>
    </table>

    <h2 class="secao">Informações Técnicas da Obra</h2>
    <table class="campos">
      <tr><td class="rotulo">Objeto:</td><td>{{{{ contrato.objeto }}}}</td></tr>
      <tr><td class="rotulo">Início:</td><td>{{{{ contrato.data_inicio }}}}</td></tr>
      <tr><td class="rotulo">Prazo:</td><td>{{{{ contrato.prazo_dias }}}} dias</td></tr>
      {{% for executor in executores %}}
      <tr><td class="rotulo">Empresa Executora:</td><td>{{{{ executor.razao_social }}}} — CNPJ {{{{ executor.cnpj }}}}</td></tr>
      <tr><td class="rotulo">ART de Execução:</td><td>{{{{ executor.art_execucao }}}}</td></tr>
      {{% endfor %}}
    </table>

    {{% if nbrs %}}
    <h2 class="secao">NBR's — Referências</h2>
    <ul class="itens">
      {{% for nbr in nbrs %}}<li>{{{{ nbr.codigo_nbr }}}}{{% if nbr.descricao %}} — {{{{ nbr.descricao }}}}{{% endif %}}</li>{{% endfor %}}
    </ul>
    {{% endif %}}
  </section>

  {{% for visita in visitas %}}
  <section class="visita">
    {{{{ marca() }}}}

    <h2 class="secao">Relatório Diário de Fiscalização — Nº {{{{ visita.seq_numero }}}}</h2>
    <table class="campos">
      <tr><td class="rotulo">Data:</td><td>{{{{ visita.data }}}}</td><td class="rotulo">Obra:</td><td>{{{{ contrato.objeto }}}}</td></tr>
      <tr><td class="rotulo">Local:</td><td>{{{{ edificacao.nome }}}}</td><td class="rotulo">Fiscal:</td><td>{{{{ fiscal.nome }}}}</td></tr>
      <tr><td class="rotulo">CREA nº:</td><td>{{{{ fiscal.crea }}}}</td><td class="rotulo">Prazo contratual:</td><td>{{{{ contrato.prazo_dias }}}} dias</td></tr>
    </table>

    <h2 class="secao">Atividades Constatadas no Dia da Visita</h2>
    <ul class="itens">
      {{% for atividade in visita.servicos_executados_lista %}}<li>{{{{ atividade }}}}</li>{{% endfor %}}
    </ul>

    {{% if visita.mao_obra %}}
    <h2 class="secao">Equipe Efetiva em Obra</h2>
    <table class="equipe">
      <thead><tr><th>Qtd.</th><th>Função</th></tr></thead>
      <tbody>
        {{% for mo in visita.mao_obra %}}<tr><td>{{{{ mo.quantidade }}}}</td><td>{{{{ mo.funcao }}}}</td></tr>{{% endfor %}}
      </tbody>
    </table>
    {{% endif %}}

    {{% if visita.medicoes %}}
    <h2 class="secao">Medições</h2>
    <table class="equipe">
      <thead><tr><th>Descrição</th><th>Quantidade</th><th>Unidade</th></tr></thead>
      <tbody>
        {{% for medicao in visita.medicoes %}}<tr><td>{{{{ medicao.descricao }}}}</td><td>{{{{ medicao.quantidade }}}}</td><td>{{{{ medicao.unidade }}}}</td></tr>{{% endfor %}}
      </tbody>
    </table>
    {{% endif %}}

    {{% if visita.observacoes %}}
    <h2 class="secao">Ocorrências / Não Conformidades</h2>
    <ul class="itens">
      {{% for ocorrencia in visita.observacoes_lista %}}<li>{{{{ ocorrencia }}}}</li>{{% endfor %}}
    </ul>
    {{% endif %}}

    {{% if visita.fotos %}}
    <h2 class="secao">Registro Fotográfico</h2>
    <div class="fotos">
      {{% for foto in visita.fotos %}}
      <figure class="foto">
        <figcaption class="legenda">{grade.get('prefixo_legenda', 'Foto')} {{{{ "%02d"|format(loop.index) }}}}</figcaption>
        <img src="{{{{ foto.data_uri }}}}" alt="{grade.get('prefixo_legenda', 'Foto')} {{{{ loop.index }}}}">
        {{% if foto.legenda %}}<div class="descricao">{{{{ foto.legenda }}}}</div>{{% endif %}}
      </figure>
      {{% endfor %}}
    </div>
    {{% endif %}}

    <div class="assinaturas">
{linhas_assinatura}
    </div>
  </section>
  {{% endfor %}}
</body>
</html>
"""


def gerar_docx(layout: dict[str, Any], destino: Path) -> None:
    """Monta o `.docx` de template com as mesmas seções e tags docxtpl do HTML."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt, RGBColor

    tipografia = layout["tipografia"]
    margens = layout["pagina"]["margens_cm"]
    cor_secao = layout["cores"]["cabecalho_secao_fundo"].lstrip("#")
    assinaturas = layout["visita"]["assinaturas"] or ["RESPONSÁVEL TÉCNICO / FISCALIZAÇÃO", "CONTRATADA", "CONTRATANTE"]

    documento = Document()
    estilo = documento.styles["Normal"]
    estilo.font.name = tipografia["familia"]
    estilo.font.size = Pt(tipografia["corpo_pt"])

    secao_pagina = documento.sections[0]
    secao_pagina.left_margin = Cm(margens["esquerda"])
    secao_pagina.right_margin = Cm(margens["direita"])
    secao_pagina.top_margin = Cm(margens["superior"])
    secao_pagina.bottom_margin = Cm(margens["inferior"])

    def cabecalho_secao(texto: str) -> None:
        paragrafo = documento.add_paragraph()
        execucao = paragrafo.add_run(texto.upper())
        execucao.bold = True
        execucao.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
        # Sombreamento de parágrafo não tem API de alto nível no python-docx.
        from docx.oxml.ns import qn
        from docx.oxml.shared import OxmlElement

        sombreamento = OxmlElement("w:shd")
        sombreamento.set(qn("w:val"), "clear")
        sombreamento.set(qn("w:fill"), cor_secao)
        paragrafo._p.get_or_add_pPr().append(sombreamento)

    def campo(rotulo: str, tag: str) -> None:
        paragrafo = documento.add_paragraph()
        paragrafo.add_run(f"{rotulo} ").bold = True
        paragrafo.add_run("{{ " + tag + " }}")

    titulo = documento.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if LOGO_PNG.is_file():
        titulo.add_run().add_picture(str(LOGO_PNG), height=Cm(1.6))
        titulo.add_run("  ")
    execucao_titulo = titulo.add_run((layout["cabecalho"]["titulo"] or {}).get("texto") or "Relatório de Fiscalização")
    execucao_titulo.bold = True
    execucao_titulo.font.size = Pt(20)

    cabecalho_secao("Informações da Edificação")
    campo("Local:", "edificacao.nome")
    campo("Endereço:", "edificacao.endereco")
    campo("Finalidade:", "edificacao.tipologia")

    cabecalho_secao("Informações Técnicas da Fiscalização")
    campo("Contrato:", "contrato.numero")
    campo("Fiscal:", "fiscal.nome")
    campo("Nº CREA:", "fiscal.crea")
    campo("ART de Fiscalização:", "contrato.art_fiscalizacao")

    cabecalho_secao("Informações Técnicas da Obra")
    campo("Objeto:", "contrato.objeto")
    campo("Início:", "contrato.data_inicio")
    campo("Prazo:", "contrato.prazo_dias")
    documento.add_paragraph("{% for executor in executores %}")
    campo("Empresa Executora:", "executor.razao_social")
    campo("ART de Execução:", "executor.art_execucao")
    documento.add_paragraph("{% endfor %}")

    cabecalho_secao("NBR's — Referências")
    documento.add_paragraph("{% for nbr in nbrs %}")
    documento.add_paragraph("{{ nbr.codigo_nbr }} — {{ nbr.descricao }}", style="List Bullet")
    documento.add_paragraph("{% endfor %}")

    documento.add_page_break()
    documento.add_paragraph("{% for visita in visitas %}")
    cabecalho_secao("Relatório Diário de Fiscalização")
    campo("Nº:", "visita.seq_numero")
    campo("Data:", "visita.data")
    campo("Local:", "edificacao.nome")
    campo("Fiscal:", "fiscal.nome")

    cabecalho_secao("Atividades Constatadas no Dia da Visita")
    documento.add_paragraph("{{ visita.servicos_executados }}")

    cabecalho_secao("Equipe Efetiva em Obra")
    tabela_equipe = documento.add_table(rows=4, cols=2)
    tabela_equipe.style = "Table Grid"
    tabela_equipe.cell(0, 0).text = "Qtd."
    tabela_equipe.cell(0, 1).text = "Função"
    # docxtpl remove a linha inteira que contém uma tag `{%tr %}` — abertura e
    # fechamento do laço precisam ficar em linhas próprias, cercando a linha modelo.
    tabela_equipe.cell(1, 0).text = "{%tr for mo in visita.mao_obra %}"
    tabela_equipe.cell(2, 0).text = "{{ mo.quantidade }}"
    tabela_equipe.cell(2, 1).text = "{{ mo.funcao }}"
    tabela_equipe.cell(3, 0).text = "{%tr endfor %}"

    cabecalho_secao("Medições")
    tabela_medicoes = documento.add_table(rows=4, cols=3)
    tabela_medicoes.style = "Table Grid"
    for indice, rotulo in enumerate(("Descrição", "Quantidade", "Unidade")):
        tabela_medicoes.cell(0, indice).text = rotulo
    tabela_medicoes.cell(1, 0).text = "{%tr for medicao in visita.medicoes %}"
    tabela_medicoes.cell(2, 0).text = "{{ medicao.descricao }}"
    tabela_medicoes.cell(2, 1).text = "{{ medicao.quantidade }}"
    tabela_medicoes.cell(2, 2).text = "{{ medicao.unidade }}"
    tabela_medicoes.cell(3, 0).text = "{%tr endfor %}"

    cabecalho_secao("Ocorrências / Não Conformidades")
    documento.add_paragraph("{{ visita.observacoes }}")

    cabecalho_secao("Registro Fotográfico")
    documento.add_paragraph("{{ visita.fotos_doc }}")

    for nome in assinaturas:
        paragrafo = documento.add_paragraph()
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragrafo.add_run(f"\n________________________\n{nome}")

    documento.add_paragraph("{% endfor %}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(str(destino))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--original", type=Path, help="Caminho do .xlsx/.xlsm original do RFO (01_output-context/).")
    parser.add_argument("--somente-layout", action="store_true", help="Extrai o layout.json sem gerar os templates.")
    argumentos = parser.parse_args(argv)

    if argumentos.original:
        try:
            layout = extrair_layout(argumentos.original)
        except LayoutExtractionError as erro:
            print(f"ERRO: {erro}", file=sys.stderr)
            return 1
        layout["extraido_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        LAYOUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        LAYOUT_JSON.write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")
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

    HTML_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    HTML_TEMPLATE.write_text(gerar_html(layout), encoding="utf-8")
    print(f"template HTML escrito em {HTML_TEMPLATE}")

    gerar_docx(layout, DOCX_TEMPLATE)
    print(f"template DOCX escrito em {DOCX_TEMPLATE}")
    print("Seções detectadas na capa:  " + ", ".join(_titulos_de_secao(layout, "capa")))
    print("Seções detectadas na visita: " + ", ".join(_titulos_de_secao(layout, "visita")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
