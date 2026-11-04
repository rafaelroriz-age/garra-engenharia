"""Testes do pipeline de templates do LTIP (BL-17, ADR-13/DEC-25, RF-06, RN-11, RNF-03).

Não dependem de `01_output-context/`: cada teste constrói um PDF sintético em
memória com a mesma geometria do original (A4, Times New Roman 12/14, rodapé do
emitente, fichas "Foto nº NN"). Assim o pipeline é verificável no CI, onde o
arquivo do cliente não existe.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.scripts.build_ltip_templates import LAYOUT_JSON, gerar_docx, gerar_html
from app.scripts.ltip_layout_extractor import LayoutExtractionError, extrair_layout

A4_LARGURA = 595.28
A4_ALTURA = 841.89
MARGEM_PT = 56.7  # 2 cm
RODAPE_EMITENTE = ("Eng. Civil - CREA-GO nº 1020613386/D-GO", "contato@garra-engenharia.com.br")


def _fluxo_de_texto(linhas: list[tuple[float, float, str, str, float]]) -> bytes:
    """Monta o content stream de uma página a partir de (x, y, fonte, texto, corpo)."""
    partes = ["BT"]
    for x, y, fonte, texto, corpo in linhas:
        escapado = texto.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        partes.append(f"/{fonte} {corpo} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({escapado}) Tj")
    partes.append("ET")
    return "\n".join(partes).encode("cp1252", errors="replace")


def _pdf_sintetico(paginas: list[list[tuple[float, float, str, str, float]]]) -> bytes:
    """PDF mínimo válido (Type1 base-14, WinAnsi) legível por `pdfplumber`.

    Escrito à mão porque nenhuma dependência do projeto gera PDF no Windows
    (WeasyPrint só roda no container) — e o teste não pode depender do original.
    """
    objetos: list[bytes] = []

    def adicionar(corpo: bytes) -> int:
        objetos.append(corpo)
        return len(objetos)

    fonte_normal = adicionar(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>"
    )
    fonte_negrito = adicionar(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Bold /Encoding /WinAnsiEncoding >>"
    )

    ids_paginas: list[int] = []
    conteudos: list[int] = []
    for linhas in paginas:
        fluxo = _fluxo_de_texto(linhas)
        conteudos.append(adicionar(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(fluxo), fluxo)))
        ids_paginas.append(0)  # reservado; preenchido abaixo

    id_pages = len(objetos) + len(paginas) + 1
    for indice, conteudo in enumerate(conteudos):
        ids_paginas[indice] = adicionar(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
            b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R >>"
            % (id_pages, A4_LARGURA, A4_ALTURA, fonte_normal, fonte_negrito, conteudo)
        )

    kids = b" ".join(b"%d 0 R" % identificador for identificador in ids_paginas)
    id_pages_real = adicionar(b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(ids_paginas)))
    assert id_pages_real == id_pages, "id reservado para /Pages divergiu"
    id_catalogo = adicionar(b"<< /Type /Catalog /Pages %d 0 R >>" % id_pages)

    saida = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for numero, corpo in enumerate(objetos, start=1):
        offsets.append(len(saida))
        saida += b"%d 0 obj\n%s\nendobj\n" % (numero, corpo)

    inicio_xref = len(saida)
    saida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for offset in offsets[1:]:
        saida += b"%010d 00000 n \n" % offset
    saida += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1,
        id_catalogo,
        inicio_xref,
    )
    return bytes(saida)


def _pagina_de_texto(titulo_numerado: str, titulo: str, corpo: str) -> list[tuple[float, float, str, str, float]]:
    """Página de texto corrido: título em negrito 14pt + parágrafos 12pt + rodapé."""
    topo = A4_ALTURA - MARGEM_PT
    linhas = [
        (MARGEM_PT, topo, "F2", titulo_numerado, 14.0),
        # Afastado o bastante para o `extract_words` não fundir número e texto do
        # título numa palavra só ("4.2.1.Localização"), o que esconderia o nível.
        (MARGEM_PT + 70, topo, "F2", titulo, 14.0),
    ]
    for indice in range(12):
        linhas.append((MARGEM_PT, topo - 24 - indice * 16, "F1", corpo, 12.0))
    # A borda direita do bloco de texto é o que define a margem direita medida.
    linhas.append((A4_LARGURA - MARGEM_PT - 40, topo - 24, "F1", "fim.", 12.0))
    for indice, linha_rodape in enumerate(RODAPE_EMITENTE):
        linhas.append((MARGEM_PT, 40 - indice * 12, "F1", linha_rodape, 9.0))
    linhas.append((A4_LARGURA - MARGEM_PT, 20, "F1", "7", 9.0))
    return linhas


def _pagina_de_fichas(numeros: tuple[int, int]) -> list[tuple[float, float, str, str, float]]:
    """Página do relatório fotográfico: duas fichas 'Foto nº NN' com os campos da ocorrência."""
    linhas: list[tuple[float, float, str, str, float]] = []
    for indice, numero in enumerate(numeros):
        base = A4_ALTURA - MARGEM_PT - indice * 380
        linhas.append((MARGEM_PT, base, "F2", f"Foto nº {numero:02d}", 12.0))
        for passo, campo in enumerate(
            ("SITUAÇÃO", "PRIORIDADE", "GRAVIDADE", "URGÊNCIA", "TENDÊNCIA", "PONTUAÇÃO",
             "CLASSIFICAÇÃO", "GRAU DE RISCO", "SISTEMA", "SUBSISTEMA", "LOCALIZAÇÃO",
             "OBSERVAÇÕES TÉCNICAS"),
        ):
            linhas.append((MARGEM_PT, base - 16 - passo * 14, "F1", campo, 10.0))
    return linhas


@pytest.fixture
def pdf_laudo(tmp_path: Path) -> Path:
    """PDF sintético com capa, corpo e relatório fotográfico, no formato do LTIP."""
    capa = [
        (150.0, A4_ALTURA - 300, "F2", "LAUDO TÉCNICO DE INSPEÇÃO PREDIAL", 45.4),
        (150.0, A4_ALTURA - 500, "F2", "Autor: Eng. Civil Esp. Fulano", 16.0),
    ]
    sumario = [(MARGEM_PT, A4_ALTURA - MARGEM_PT, "F1", "Sumário", 12.0)]
    paginas = [capa, sumario, sumario, sumario, sumario]
    paginas += [
        _pagina_de_texto("1.", "INTRODUÇÃO", "Texto corrido do laudo tecnico."),
        _pagina_de_texto("1.1.", "Histórico", "Texto corrido do laudo tecnico."),
        _pagina_de_texto("2.", "CONSIDERAÇÕES PRELIMINARES", "Texto corrido do laudo tecnico."),
        _pagina_de_texto("4.2.1.", "Localização", "Texto corrido do laudo tecnico."),
    ]
    paginas += [_pagina_de_fichas((1, 2)), _pagina_de_fichas((3, 4))]

    destino = tmp_path / "laudo_sintetico.pdf"
    destino.write_bytes(_pdf_sintetico(paginas))
    return destino


@pytest.fixture
def layout(pdf_laudo: Path) -> dict:
    return extrair_layout(pdf_laudo, pagina_inicial_corpo=5, amostra_paginas=10)


def test_extrai_geometria_da_pagina(layout: dict) -> None:
    assert layout["tipo_documento"] == "LTIP"
    assert layout["pagina"]["tamanho"] == "A4"
    assert layout["pagina"]["orientacao"] == "portrait"
    margens = layout["pagina"]["margens_cm"]
    assert margens["esquerda"] == pytest.approx(2.0, abs=0.1)
    assert margens["direita"] == pytest.approx(2.0, abs=0.2)


def test_mede_tipografia_de_corpo_e_titulo(layout: dict) -> None:
    # O PDF sintético usa a base-14 `Times-Roman`; o original do cliente usa
    # `TimesNewRomanPSMT`. Em ambos os casos o extrator devolve a família CSS.
    assert layout["tipografia"]["familia"] == "Times"
    assert layout["tipografia"]["corpo_pt"] == 12.0
    assert layout["tipografia"]["titulo_pt"] == 14.0


def test_reconhece_hierarquia_de_titulos_numerados(layout: dict) -> None:
    niveis = {titulo["nivel"] for titulo in layout["titulos"]}
    assert {1, 2, 3}.issubset(niveis)


def test_rodape_guarda_apenas_a_marca_do_emitente(layout: dict) -> None:
    assert layout["rodape"]["linhas"] == list(RODAPE_EMITENTE)
    assert layout["rodape"]["numeracao_pagina"] is True


def test_layout_nao_carrega_dado_do_exemplar_do_cliente(layout: dict) -> None:
    """Regressão de privacidade (OWASP A02): o layout.json é versionado."""
    serializado = json.dumps(layout, ensure_ascii=False)
    assert "laudo_sintetico" not in serializado
    assert "arquivo" not in layout["origem"]
    assert len(layout["origem"]["sha256"]) == 64


def test_extrai_grade_do_relatorio_fotografico(layout: dict) -> None:
    ficha = layout["relatorio_fotografico"]
    assert ficha["fichas_por_pagina"] == 2
    assert ficha["rotulo_foto"] == "Foto nº"
    assert "GRAU DE RISCO" in ficha["campos"]
    assert "SUBSISTEMA" in ficha["campos"]


def test_original_ausente_falha_explicitamente(tmp_path: Path) -> None:
    with pytest.raises(LayoutExtractionError, match="não encontrado"):
        extrair_layout(tmp_path / "inexistente.pdf")


def test_pdf_sem_ficha_fotografica_falha(tmp_path: Path) -> None:
    destino = tmp_path / "sem_fotos.pdf"
    destino.write_bytes(
        _pdf_sintetico([[(MARGEM_PT, 700.0, "F1", "Texto corrido.", 12.0)] for _ in range(12)])
    )
    with pytest.raises(LayoutExtractionError, match="ficha fotográfica"):
        extrair_layout(destino, pagina_inicial_corpo=5, amostra_paginas=6)


def test_html_gerado_respeita_as_medidas_e_itera_por_sistema(layout: dict) -> None:
    html = gerar_html(layout)
    margens = layout["pagina"]["margens_cm"]
    assert "size: A4 portrait" in html
    assert f"margin: {margens['superior']}cm" in html
    assert f"font-size: {layout['tipografia']['corpo_pt']}pt" in html
    # RN-11: fotos organizadas por Sistema e, dentro dele, por ocorrência.
    assert "{% for sistema in sistemas %}" in html
    # As fichas saem em linhas (`batch`), que preservam a ordem das ocorrências (T20).
    assert "{% for linha in sistema.ocorrencias|batch(" in html
    assert "{% for ocorrencia in linha %}" in html
    assert "OBSERVAÇÕES TÉCNICAS" in html
    assert RODAPE_EMITENTE[0] in html


def test_html_gerado_agrupa_fichas_em_linhas_sem_flex(layout: dict) -> None:
    """T20/DEC-40: o flex único por sistema tinha custo quadrático no WeasyPrint."""
    html = gerar_html(layout)
    por_linha = layout["relatorio_fotografico"]["fichas_por_pagina"]
    assert f"sistema.ocorrencias|batch({por_linha})" in html
    assert "table-layout: fixed" in html
    assert "display: flex" not in html
    assert '<td class="ficha">' in html


def test_docx_gerado_tem_blocos_balanceados(layout: dict, tmp_path: Path) -> None:
    from docxtpl import DocxTemplate

    destino = tmp_path / "ltip_template.docx"
    gerar_docx(layout, destino)

    template = DocxTemplate(destino)
    template.init_docx()
    tags = re.findall(r"\{%[^%]*%\}", template.patch_xml(template.get_xml()))
    assert sum(1 for tag in tags if " for " in tag) == sum(1 for tag in tags if "endfor" in tag)
    assert any("sistemas" in tag for tag in tags)


def test_layout_versionado_esta_em_dia_com_o_schema() -> None:
    """O `layout.json` versionado precisa continuar legível pelo gerador atual."""
    if not LAYOUT_JSON.is_file():
        pytest.skip("layout.json ainda não gerado nesta máquina.")
    layout_versionado = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))
    assert layout_versionado["versao_schema"] == 1
    assert layout_versionado["tipo_documento"] == "LTIP"
    assert "arquivo" not in layout_versionado["origem"]
    assert gerar_html(layout_versionado).startswith("<!DOCTYPE html>")
