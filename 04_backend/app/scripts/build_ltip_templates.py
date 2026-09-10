"""Deriva os templates do LTIP (HTML/Jinja2 + DOCX) a partir do PDF original do cliente.

Pipeline determinístico de ADR-13/DEC-25, irmão de `build_rfo_templates` — a
diferença é a origem: o RFO nasce de planilha, o LTIP do PDF final.

    01_output-context/<laudo>.pdf
        -> app/scripts/ltip_layout_extractor.extrair_layout()
        -> 04_backend/templates/ltip/layout.json             (versionado)
        -> 04_backend/templates/ltip/ltip_template.html.j2   (WeasyPrint, ADR-01)
        -> 04_backend/templates/ltip/ltip_template.docx      (docxtpl, ADR-04)

Uso:

    python -m app.scripts.build_ltip_templates \
        --original "../01_output-context/Laudo Técnico de Inspeção Predial 2026 - Cond. Cortina D'Ampezzo.pdf"

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

from app.scripts.ltip_layout_extractor import LayoutExtractionError, extrair_layout

TEMPLATES_LTIP_DIR = Path(__file__).resolve().parents[2] / "templates" / "ltip"
LAYOUT_JSON = TEMPLATES_LTIP_DIR / "layout.json"
HTML_TEMPLATE = TEMPLATES_LTIP_DIR / "ltip_template.html.j2"
DOCX_TEMPLATE = TEMPLATES_LTIP_DIR / "ltip_template.docx"

CABECALHO_GERADO = (
    "ARQUIVO GERADO — não editar à mão. "
    "Produzido por `python -m app.scripts.build_ltip_templates` a partir de "
    "templates/ltip/layout.json (ADR-13/DEC-25)."
)

#: Seções fixas do corpo do laudo, na ordem do original. O conteúdo é livre
#: (vem do banco), mas a espinha dorsal do documento é padronizada — é o que
#: garante a fidelidade estrutural exigida por RNF-03.
SECOES_CORPO = (
    ("introducao", "1. INTRODUÇÃO"),
    ("consideracoes_preliminares", "2. CONSIDERAÇÕES PRELIMINARES"),
    ("objetivo", "3. OBJETIVO"),
    ("objeto", "4. OBJETO"),
    ("metodologia", "5. METODOLOGIA"),
    ("documentacao_analisada", "6. DOCUMENTAÇÃO ANALISADA"),
)


def _fonte_do_nivel(layout: dict[str, Any], nivel: int, padrao: float) -> float:
    for titulo in layout.get("titulos", []):
        if titulo["nivel"] == nivel:
            return titulo["fonte_pt"]
    return padrao


def gerar_html(layout: dict[str, Any]) -> str:
    """Monta o `.html.j2` respeitando margens, fonte e rodapé medidos no original."""
    pagina = layout["pagina"]
    margens = pagina["margens_cm"]
    tipografia = layout["tipografia"]
    cores = layout["cores"]
    capa = layout["capa"]
    rodape = layout["rodape"]
    ficha = layout["relatorio_fotografico"]

    fonte_h1 = _fonte_do_nivel(layout, 1, tipografia["titulo_pt"])
    fonte_h2 = _fonte_do_nivel(layout, 2, tipografia["titulo_pt"])
    fonte_h3 = _fonte_do_nivel(layout, 3, tipografia["titulo_pt"])
    largura_ficha = round(100 / max(ficha["fichas_por_pagina"], 1) - 2, 2)
    linhas_rodape = "\\A ".join(rodape["linhas"])
    secoes_html = "\n".join(
        f'  <section class="capitulo">\n'
        f"    <h1>{titulo}</h1>\n"
        f"    {{% for paragrafo in {chave}_paragrafos %}}<p>{{{{ paragrafo }}}}</p>{{% endfor %}}\n"
        f"  </section>"
        for chave, titulo in SECOES_CORPO
    )

    return f"""<!DOCTYPE html>
{{#
  {CABECALHO_GERADO}

  Layout derivado do PDF original sha256 {layout['origem']['sha256'][:16]}…
  ({layout['origem']['paginas']} páginas medidas). O nome do arquivo não é versionado:
  identifica o cliente inspecionado (OWASP A02).
#}}
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>{capa['titulo']['texto']} — {{{{ edificacao.nome }}}}</title>
<style>
  @page {{
    size: {pagina['tamanho']} {pagina['orientacao']};
    margin: {margens['superior']}cm {margens['direita']}cm {margens['inferior']}cm {margens['esquerda']}cm;
    @bottom-center {{
      content: "{linhas_rodape}";
      font-family: {tipografia['familia']}, serif;
      font-size: {tipografia['legenda_pt']}pt;
      white-space: pre-line;
    }}
    @bottom-right {{
      content: counter(page);
      font-family: {tipografia['familia']}, serif;
      font-size: {tipografia['legenda_pt']}pt;
    }}
  }}
  @page capa {{ margin: 0; @bottom-center {{ content: none; }} @bottom-right {{ content: none; }} }}
  body {{
    font-family: {tipografia['familia']}, "DejaVu Serif", serif;
    font-size: {tipografia['corpo_pt']}pt;
    color: {cores['texto']};
    margin: 0;
    text-align: justify;
  }}
  h1 {{ font-size: {fonte_h1}pt; font-weight: bold; text-transform: uppercase; margin: 0.5cm 0 0.25cm 0; }}
  h2 {{ font-size: {fonte_h2}pt; font-weight: bold; margin: 0.4cm 0 0.2cm 0; }}
  h3 {{ font-size: {fonte_h3}pt; font-weight: bold; margin: 0.3cm 0 0.15cm 0; }}
  p {{ margin: 0 0 0.2cm 0; line-height: 1.35; }}
  .capa {{ page: capa; height: 100%; position: relative; text-align: center; }}
  .capa .logo {{ width: {round(capa['logo']['largura_pt'] / 28.35, 2) if capa['logo'] else 7.6}cm; margin-top: {round((capa['logo']['topo_pt'] if capa['logo'] else 0) / 28.35, 2)}cm; }}
  .capa .titulo {{
    font-family: {capa['titulo']['familia']}, sans-serif;
    font-size: {capa['titulo']['fonte_pt']}pt;
    font-weight: bold;
    line-height: 1.1;
    margin-top: 6cm;
  }}
  .capa .autoria {{ font-family: {capa['titulo']['familia']}, sans-serif; font-size: 16pt; font-weight: bold; margin-top: 4cm; }}
  .capitulo {{ page-break-before: always; }}
  figure.figura {{ margin: 0.3cm 0; text-align: center; }}
  figure.figura img {{ max-width: 100%; }}
  figure.figura figcaption {{ font-size: {tipografia['legenda_pt']}pt; font-style: italic; }}
  /* Relatório fotográfico por sistema (RN-11): uma ficha por ocorrência. */
  .sistema {{ page-break-before: always; }}
  .fichas {{ display: flex; flex-wrap: wrap; gap: 0.4cm; }}
  .ficha {{ width: {largura_ficha}%; page-break-inside: avoid; border: 0.5pt solid #999; }}
  .ficha .rotulo-foto {{
    background: {cores['cabecalho_secao_fundo']};
    font-weight: bold;
    text-align: center;
    padding: 2pt;
  }}
  .ficha img {{ width: 100%; display: block; }}
  .ficha table {{ width: 100%; border-collapse: collapse; font-size: {tipografia['legenda_pt']}pt; }}
  .ficha th, .ficha td {{ border: 0.5pt solid #999; padding: 1.5pt 3pt; text-align: left; vertical-align: top; }}
  .ficha th {{ background: {cores['cabecalho_secao_fundo']}; white-space: nowrap; }}
  .risco-CRITICO {{ font-weight: bold; }}
</style>
</head>
<body>
  <section class="capa">
    {{% if logo_data_uri %}}<img class="logo" src="{{{{ logo_data_uri }}}}" alt="Garra Engenharia">{{% endif %}}
    <div class="titulo">{capa['titulo']['texto']}</div>
    <div class="autoria">
      Autor:<br>
      {{{{ fiscal.nome }}}}<br>
      CREA nº {{{{ fiscal.crea }}}}<br>
      {{{{ data_emissao }}}}
    </div>
  </section>

{secoes_html}

  <section class="capitulo">
    <h1>7. RELATÓRIO FOTOGRÁFICO POR SISTEMA</h1>
    <p>
      As ocorrências abaixo estão organizadas por Sistema Predial e, dentro de cada sistema,
      por Subsistema (RN-11). O Grau de Risco segue o método GUT (RN-04).
    </p>
  </section>

  {{% for sistema in sistemas %}}
  <section class="sistema">
    <h2>7.{{{{ loop.index }}}}. {{{{ sistema.nome }}}}</h2>
    <div class="fichas">
      {{% for ocorrencia in sistema.ocorrencias %}}
      <div class="ficha">
        <div class="rotulo-foto">{ficha['rotulo_foto']} {{{{ "%02d"|format(ocorrencia.seq_numero) }}}}</div>
        {{% if ocorrencia.foto_data_uri %}}<img src="{{{{ ocorrencia.foto_data_uri }}}}" alt="{ficha['rotulo_foto']} {{{{ ocorrencia.seq_numero }}}}">{{% endif %}}
        <table>
          <tr><th>SITUAÇÃO</th><td>{{{{ ocorrencia.situacao }}}}</td></tr>
          <tr><th>PRIORIDADE</th><td>{{{{ ocorrencia.prioridade if ocorrencia.prioridade is not none else "—" }}}}</td></tr>
          <tr><th>GRAVIDADE</th><td>{{{{ ocorrencia.gut_gravidade or "—" }}}}</td></tr>
          <tr><th>URGÊNCIA</th><td>{{{{ ocorrencia.gut_urgencia or "—" }}}}</td></tr>
          <tr><th>TENDÊNCIA</th><td>{{{{ ocorrencia.gut_tendencia or "—" }}}}</td></tr>
          <tr><th>PONTUAÇÃO</th><td>{{{{ ocorrencia.pontuacao_gut }}}}</td></tr>
          <tr><th>CLASSIFICAÇÃO</th><td>{{{{ ocorrencia.classificacao }}}}</td></tr>
          <tr><th>TIPO</th><td>{{{{ ocorrencia.tipo_anomalia or ocorrencia.tipo_falha or "—" }}}}</td></tr>
          <tr><th>GRAU DE RISCO</th><td class="risco-{{{{ ocorrencia.grau_risco }}}}">{{{{ ocorrencia.grau_risco }}}}</td></tr>
          <tr><th>SUBSISTEMA</th><td>{{{{ ocorrencia.subsistema or "—" }}}}</td></tr>
          <tr><th>LOCALIZAÇÃO</th><td>{{{{ ocorrencia.localizacao or "—" }}}}</td></tr>
          <tr><th>OBSERVAÇÕES TÉCNICAS</th><td>{{{{ ocorrencia.descricao or "—" }}}}</td></tr>
        </table>
      </div>
      {{% endfor %}}
    </div>
  </section>
  {{% endfor %}}

  <section class="capitulo">
    <h1>8. CONCLUSÃO</h1>
    {{% for paragrafo in conclusao_paragrafos %}}<p>{{{{ paragrafo }}}}</p>{{% endfor %}}
    <p>
      {{{{ fiscal.nome }}}}<br>
      Eng. Civil — CREA nº {{{{ fiscal.crea }}}}<br>
      ART nº {{{{ contrato.art_fiscalizacao }}}}
    </p>
  </section>
</body>
</html>
"""


def gerar_docx(layout: dict[str, Any], destino: Path) -> None:
    """Monta o `.docx` de template com as mesmas seções e tags docxtpl do HTML."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    tipografia = layout["tipografia"]
    margens = layout["pagina"]["margens_cm"]
    capa = layout["capa"]
    ficha = layout["relatorio_fotografico"]

    documento = Document()
    estilo = documento.styles["Normal"]
    estilo.font.name = tipografia["familia"]
    estilo.font.size = Pt(tipografia["corpo_pt"])

    secao_pagina = documento.sections[0]
    secao_pagina.left_margin = Cm(margens["esquerda"])
    secao_pagina.right_margin = Cm(margens["direita"])
    secao_pagina.top_margin = Cm(margens["superior"])
    secao_pagina.bottom_margin = Cm(margens["inferior"])

    rodape = secao_pagina.footer.paragraphs[0]
    rodape.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rodape.text = "\n".join(layout["rodape"]["linhas"])
    for execucao in rodape.runs:
        execucao.font.size = Pt(tipografia["legenda_pt"])

    def titulo(texto: str, tamanho: float) -> None:
        paragrafo = documento.add_paragraph()
        execucao = paragrafo.add_run(texto)
        execucao.bold = True
        execucao.font.size = Pt(tamanho)

    capa_titulo = documento.add_paragraph()
    capa_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    execucao_capa = capa_titulo.add_run(capa["titulo"]["texto"])
    execucao_capa.bold = True
    execucao_capa.font.size = Pt(min(capa["titulo"]["fonte_pt"], 45))

    autoria = documento.add_paragraph()
    autoria.alignment = WD_ALIGN_PARAGRAPH.CENTER
    autoria.add_run("Autor: {{ fiscal.nome }} — CREA nº {{ fiscal.crea }} — {{ data_emissao }}")
    documento.add_page_break()

    for chave, texto_titulo in SECOES_CORPO:
        titulo(texto_titulo, _fonte_do_nivel(layout, 1, tipografia["titulo_pt"]))
        documento.add_paragraph("{%p for paragrafo in " + chave + "_paragrafos %}")
        documento.add_paragraph("{{ paragrafo }}")
        documento.add_paragraph("{%p endfor %}")

    titulo("7. RELATÓRIO FOTOGRÁFICO POR SISTEMA", _fonte_do_nivel(layout, 1, tipografia["titulo_pt"]))
    documento.add_paragraph("{%p for sistema in sistemas %}")
    documento.add_paragraph("{{ sistema.nome }}")
    documento.add_paragraph("{%p for ocorrencia in sistema.ocorrencias %}")
    documento.add_paragraph(ficha["rotulo_foto"] + ' {{ "%02d"|format(ocorrencia.seq_numero) }}')

    # A tabela da ficha é o modelo iterado: 4 linhas (cabeçalho, `for`, dados, `endfor`)
    # porque `{%tr %}` remove a linha inteira em que aparece (armadilha do docxtpl).
    tabela = documento.add_table(rows=0, cols=2)
    tabela.style = "Table Grid"
    for rotulo, expressao in (
        ("SITUAÇÃO", "{{ ocorrencia.situacao }}"),
        ("PRIORIDADE", "{{ ocorrencia.prioridade }}"),
        ("GRAVIDADE", "{{ ocorrencia.gut_gravidade }}"),
        ("URGÊNCIA", "{{ ocorrencia.gut_urgencia }}"),
        ("TENDÊNCIA", "{{ ocorrencia.gut_tendencia }}"),
        ("PONTUAÇÃO", "{{ ocorrencia.pontuacao_gut }}"),
        ("CLASSIFICAÇÃO", "{{ ocorrencia.classificacao }}"),
        ("TIPO", "{{ ocorrencia.tipo_anomalia or ocorrencia.tipo_falha }}"),
        ("GRAU DE RISCO", "{{ ocorrencia.grau_risco }}"),
        ("SUBSISTEMA", "{{ ocorrencia.subsistema }}"),
        ("LOCALIZAÇÃO", "{{ ocorrencia.localizacao }}"),
        ("OBSERVAÇÕES TÉCNICAS", "{{ ocorrencia.descricao }}"),
    ):
        linha = tabela.add_row().cells
        linha[0].paragraphs[0].add_run(rotulo).bold = True
        linha[1].text = expressao

    documento.add_paragraph("{%p endfor %}")
    documento.add_paragraph("{%p endfor %}")

    titulo("8. CONCLUSÃO", _fonte_do_nivel(layout, 1, tipografia["titulo_pt"]))
    documento.add_paragraph("{%p for paragrafo in conclusao_paragrafos %}")
    documento.add_paragraph("{{ paragrafo }}")
    documento.add_paragraph("{%p endfor %}")
    documento.add_paragraph("{{ fiscal.nome }} — CREA nº {{ fiscal.crea }} — ART nº {{ contrato.art_fiscalizacao }}")

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(destino)


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
    parser = argparse.ArgumentParser(description="Gera os templates do LTIP a partir do PDF original.")
    parser.add_argument("--original", type=Path, default=None, help="Caminho do PDF original do laudo.")
    argumentos = parser.parse_args(argv)

    try:
        layout = _carregar_layout(argumentos.original)
    except LayoutExtractionError as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    TEMPLATES_LTIP_DIR.mkdir(parents=True, exist_ok=True)
    if argumentos.original is not None:
        layout["gerado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        LAYOUT_JSON.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"layout.json atualizado a partir do original informado (sha256 {layout['origem']['sha256'][:16]}…)")

    HTML_TEMPLATE.write_text(gerar_html(layout), encoding="utf-8")
    gerar_docx(layout, DOCX_TEMPLATE)
    print(f"gerados: {HTML_TEMPLATE.name}, {DOCX_TEMPLATE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
