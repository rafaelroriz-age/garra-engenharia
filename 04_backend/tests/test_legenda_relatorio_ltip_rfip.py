"""Só legenda aprovada entra no LTIP e no RFIP (RN-16/RN-17, DEC-37 DP-9; BL-36).

Sem banco: objetos simples e contexto sintético. A regra é aplicada em
`_normalizar_ocorrencia`, usada pelos caminhos de PDF e DOCX dos dois pipelines;
os testes de caminho espionam o contexto normalizado para provar isso. O render
de PDF só roda onde o WeasyPrint carrega.
"""
from __future__ import annotations

import io
from types import SimpleNamespace

import pytest
from PIL import Image

from app.services.report_generator import ltip_pipeline, rfip_pipeline
from app.services.report_generator.legenda_foto import legenda_para_relatorio

try:
    import weasyprint  # noqa: F401

    WEASYPRINT_OK = True
except Exception:  # GTK/libgobject ausente no Windows local
    WEASYPRINT_OK = False

IA = "Sugestão automática da IA"
PIPELINES = pytest.mark.parametrize("modulo", [ltip_pipeline, rfip_pipeline], ids=["ltip", "rfip"])


def _foto(chave, legenda=None, ia=None, status=None):
    return {"storage_key": chave, "legenda": legenda, "legenda_ia_sugerida": ia, "status_validacao_ia": status}


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), (10, 20, 30)).save(buf, format="JPEG")
    return buf.getvalue()


def _contexto(fotos: list[dict]) -> dict:
    ocorrencias = [
        {"seq_numero": i + 1, "sistema": "Elétrico", "fotos": [f], "descricao": "d"} for i, f in enumerate(fotos)
    ]
    return {"ocorrencias": ocorrencias, "responsavel": {}}


def _legendas(ctx: dict) -> list[str]:
    return [o["fotos"][0]["legenda"] for s in ctx["sistemas"] for o in s["ocorrencias"]]


FOTOS = [
    _foto("k/rascunho_sem_manual", None, IA, "rascunho"),
    _foto("k/rascunho_com_manual", "Anterior manual", IA, "rascunho"),
    _foto("k/aprovada", "Legenda aprovada", IA, "aprovada"),
    _foto("k/manual", "Legenda manual"),
    _foto("k/espacos", "   "),
]
ESPERADO = ["", "Anterior manual", "Legenda aprovada", "Legenda manual", ""]


@PIPELINES
def test_normalizar_contexto_aplica_o_helper(modulo):
    ctx = modulo.normalizar_contexto(_contexto([dict(f) for f in FOTOS]))
    assert _legendas(ctx) == ESPERADO
    assert all(IA not in legenda for legenda in _legendas(ctx))


@PIPELINES
def test_nao_muta_contexto_original(modulo):
    original = _contexto([_foto("k/a", None, IA, "rascunho")])
    modulo.normalizar_contexto(original)
    assert original["ocorrencias"][0]["fotos"][0]["legenda"] is None


def test_helper_com_simplenamespace():
    def foto(legenda, status, ia=IA):
        return SimpleNamespace(legenda=legenda, legenda_ia_sugerida=ia, status_validacao_ia=status)

    assert legenda_para_relatorio(foto(None, "rascunho")) == ""
    assert legenda_para_relatorio(foto("Ok", "aprovada")) == "Ok"
    assert legenda_para_relatorio(foto("Manual", None, ia=None)) == "Manual"


@PIPELINES
def test_caminho_html_usa_contexto_normalizado(modulo, monkeypatch):
    capturado = []
    real = modulo.normalizar_contexto

    def espiao(c):
        r = real(c)
        capturado.append(r)
        return r

    monkeypatch.setattr(modulo, "normalizar_contexto", espiao)
    modulo.renderizar_html(_contexto([_foto("k/1", None, IA, "rascunho")]), {"k/1": _jpeg()})
    assert _legendas(capturado[0]) == [""]


@PIPELINES
def test_caminho_docx_usa_contexto_normalizado(modulo, monkeypatch, tmp_path):
    from docxtpl import DocxTemplate

    recebido = []
    render_real = DocxTemplate.render

    def espiao(self, contexto, *args, **kwargs):
        recebido.append(contexto)
        return render_real(self, contexto, *args, **kwargs)

    monkeypatch.setattr(DocxTemplate, "render", espiao)
    fotos = [_foto("k/1", None, IA, "rascunho"), _foto("k/2", "Aprovada", IA, "aprovada")]
    modulo.gerar_docx(_contexto(fotos), {"k/1": _jpeg(), "k/2": _jpeg()}, tmp_path / "o.docx")
    assert _legendas(recebido[0]) == ["", "Aprovada"]


@pytest.mark.skipif(not WEASYPRINT_OK, reason="WeasyPrint/GTK indisponível neste ambiente")
@PIPELINES
def test_caminho_pdf_gera_arquivo(modulo, tmp_path):
    modulo.gerar_pdf(_contexto([_foto("k/1", None, IA, "rascunho")]), {"k/1": _jpeg()}, tmp_path / "o.pdf")
    assert (tmp_path / "o.pdf").stat().st_size > 0
