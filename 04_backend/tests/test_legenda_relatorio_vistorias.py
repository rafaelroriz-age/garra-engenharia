"""Regra «só legenda aprovada entra no relatório» nas Vistorias (BL-36; RN-16/RN-17, DEC-37 DP-9).

Cobre Cautelar (`figuras`) e Residencial (`fotos`): sugestão de IA em
`rascunho` ou `aprovada` nunca é impressa (a aprovação copia o texto para
`legenda`); legenda manual aparece. Dados sintéticos, sem banco. HTML e DOCX
rodam em qualquer máquina; o PDF só onde o WeasyPrint carrega.
"""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from app.services.report_generator import vistoria_cautelar_pipeline as cautelar
from app.services.report_generator import vistoria_residencial_pipeline as residencial

IA_RASCUNHO = "SUGESTAO-IA-RASCUNHO-XYZ"
IA_APROVADA = "SUGESTAO-IA-APROVADA-XYZ"
MANUAL = "LEGENDA-MANUAL-XYZ"
APROVADA_TEXTO = "LEGENDA-APROVADA-XYZ"  # texto aprovado, já copiado para `legenda`

try:
    import weasyprint  # noqa: F401

    WEASYPRINT_OK = True
except Exception:  # OSError (GTK/Pango ausentes) ou ImportError
    WEASYPRINT_OK = False

sem_weasyprint = pytest.mark.skipif(not WEASYPRINT_OK, reason="WeasyPrint/GTK indisponível neste ambiente")


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), (120, 120, 120)).save(buf, format="JPEG")
    return buf.getvalue()


def _itens() -> list[dict]:
    return [
        # IA em rascunho, sem legenda aprovada: nada de IA no relatório
        {"legenda": None, "legenda_ia_sugerida": IA_RASCUNHO, "status_validacao_ia": "rascunho", "storage_key": "f/1.jpg"},
        # IA aprovada: o texto aprovado está em `legenda`; a sugestão crua não é impressa
        {"legenda": APROVADA_TEXTO, "legenda_ia_sugerida": IA_APROVADA, "status_validacao_ia": "aprovada", "storage_key": "f/2.jpg"},
        # manual
        {"legenda": MANUAL, "legenda_ia_sugerida": None, "status_validacao_ia": None, "storage_key": "f/3.jpg"},
    ]


FOTOS = {f"f/{i}.jpg": _jpeg() for i in (1, 2, 3)}


def _ctx_cautelar() -> dict:
    return {"data_emissao": "2026-11-04", "figuras": _itens()}


def _ctx_residencial() -> dict:
    return {"data_emissao": "2026-11-04", "fotos": _itens()}


def _texto_docx(caminho: Path) -> str:
    from docx import Document

    doc = Document(str(caminho))
    partes = [p.text for p in doc.paragraphs]
    for tabela in doc.tables:
        for linha in tabela.rows:
            partes.extend(c.text for c in linha.cells)
    return "\n".join(partes)


PIPELINES = [
    pytest.param(cautelar, _ctx_cautelar, "figuras", id="cautelar"),
    pytest.param(residencial, _ctx_residencial, "fotos", id="residencial"),
]


@pytest.mark.parametrize(("pipeline", "fabrica", "chave"), PIPELINES)
def test_normalizar_usa_so_legenda(pipeline, fabrica, chave):
    itens = pipeline.normalizar_contexto(fabrica())[chave]
    assert itens[0]["legenda"] == pipeline.VAZIO  # rascunho de IA não vira legenda
    assert itens[1]["legenda"] == APROVADA_TEXTO
    assert itens[2]["legenda"] == MANUAL


@pytest.mark.parametrize(("pipeline", "fabrica", "chave"), PIPELINES)
def test_normalizar_nao_muta_contexto(pipeline, fabrica, chave):
    ctx = fabrica()
    pipeline.normalizar_contexto(ctx)
    assert ctx[chave][0]["legenda"] is None


@pytest.mark.parametrize(("pipeline", "fabrica", "chave"), PIPELINES)
def test_html_ia_rascunho_nao_aparece_aprovada_e_manual_aparecem(pipeline, fabrica, chave):
    html = pipeline.renderizar_html(fabrica(), FOTOS)
    assert IA_RASCUNHO not in html
    assert IA_APROVADA not in html
    assert APROVADA_TEXTO in html
    assert MANUAL in html


@pytest.mark.parametrize(("pipeline", "fabrica", "chave"), PIPELINES)
def test_docx_ia_rascunho_nao_aparece_aprovada_e_manual_aparecem(pipeline, fabrica, chave, tmp_path):
    destino = tmp_path / "saida.docx"
    pipeline.gerar_docx(fabrica(), FOTOS, destino)
    texto = _texto_docx(destino)
    assert IA_RASCUNHO not in texto
    assert IA_APROVADA not in texto
    assert APROVADA_TEXTO in texto
    assert MANUAL in texto


@sem_weasyprint
@pytest.mark.parametrize(("pipeline", "fabrica", "chave"), PIPELINES)
def test_pdf_ia_rascunho_nao_aparece_aprovada_e_manual_aparecem(pipeline, fabrica, chave, tmp_path):
    pdfplumber = pytest.importorskip("pdfplumber")
    destino = tmp_path / "saida.pdf"
    pipeline.gerar_pdf(fabrica(), FOTOS, destino)
    with pdfplumber.open(str(destino)) as pdf:
        texto = "\n".join((p.extract_text() or "") for p in pdf.pages)
    assert IA_RASCUNHO not in texto
    assert IA_APROVADA not in texto
    assert APROVADA_TEXTO in texto
    assert MANUAL in texto
