"""Testes do `url_fetcher` das fotos nos pipelines RFO/cautelar/residencial (DEC-41, item B).

Não precisam de WeasyPrint nem de PostgreSQL, exceto os testes marcados com
`importorskip`, que só exercitam a classe `URLFetcher` (puro Python, sem GTK).
"""
from __future__ import annotations

import io

import pytest
from PIL import Image

from app.services.report_generator import vistoria_cautelar_pipeline as cautelar
from app.services.report_generator import vistoria_residencial_pipeline as residencial
from app.services.report_generator.foto_fetcher import (
    ESQUEMA_FOTO,
    RegistroDeFotos,
    UrlNaoPermitida,
    criar_url_fetcher,
    mime_da_imagem,
)


def _exigir_weasyprint() -> None:
    """Pula onde o WeasyPrint não carrega (GTK/Pango ausentes no Windows)."""
    try:
        import weasyprint.urls  # noqa: F401
    except (ImportError, OSError) as exc:
        pytest.skip(f"WeasyPrint indisponível neste ambiente: {type(exc).__name__}")


def _jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), (10, 120, 200)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_registro_emite_urls_sequenciais_e_resolve():
    registro = RegistroDeFotos()
    a, b = registro.registrar(b"aaa"), registro.registrar(b"bbb")
    assert (a, b) == (f"{ESQUEMA_FOTO}0", f"{ESQUEMA_FOTO}1")
    assert registro.resolver(b) == b"bbb"
    assert len(registro) == 2


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "file:///C:/Windows/win.ini",
        "http://169.254.169.254/latest/meta-data/",
        "https://example.com/x.png",
        "/etc/passwd",
        "garra-foto:5",  # não registrada
        "garra-foto:-1",
        "garra-foto:",
        "garra-foto:abc",
        "garra-foto:0 ",
        "garra-foto:../0",
    ],
)
def test_registro_rejeita_urls_nao_registradas(url):
    registro = RegistroDeFotos()
    registro.registrar(b"x")
    with pytest.raises(UrlNaoPermitida):
        registro.resolver(url)


def test_mime_da_imagem():
    assert mime_da_imagem(b"\x89PNG\r\n\x1a\nxxxx") == "image/png"
    assert mime_da_imagem(_jpeg()) == "image/jpeg"


def test_fetcher_entrega_so_o_registrado_e_bloqueia_o_resto():
    _exigir_weasyprint()
    registro = RegistroDeFotos()
    url = registro.registrar(_jpeg())
    fetcher = criar_url_fetcher(registro)
    assert fetcher is not None
    assert fetcher.fetch(url) is not None
    for proibida in ("file:///etc/passwd", "http://127.0.0.1/", "garra-foto:99"):
        with pytest.raises(UrlNaoPermitida):
            fetcher.fetch(proibida)


def test_fetcher_aceita_data_uri_do_logo():
    _exigir_weasyprint()
    fetcher = criar_url_fetcher(RegistroDeFotos())
    assert fetcher.fetch("data:image/svg+xml;base64,PHN2Zy8+") is not None


def test_cautelar_renderiza_com_registro_sem_base64_de_foto():
    ctx = {"figuras": [{"numero": 1, "storage_key": "f/1.jpg", "legenda": "x"}]}
    registro = RegistroDeFotos()
    html = cautelar._renderizar(ctx, {"f/1.jpg": _jpeg()}, registro)
    assert f'src="{ESQUEMA_FOTO}0"' in html
    assert len(registro) == 1
    assert "data:image/jpeg" not in html


def test_cautelar_renderizar_html_segue_autocontido():
    ctx = {"figuras": [{"numero": 1, "storage_key": "f/1.jpg"}]}
    html = cautelar.renderizar_html(ctx, {"f/1.jpg": _jpeg()})
    assert "data:image/jpeg;base64," in html
    assert ESQUEMA_FOTO not in html


def test_residencial_renderiza_com_registro_sem_base64_de_foto():
    ctx = {"fotos": [{"numero": 1, "storage_key": "f/1.jpg", "legenda": "x"}]}
    html = residencial._renderizar(ctx, {"f/1.jpg": _jpeg()}, RegistroDeFotos())
    assert f'src="{ESQUEMA_FOTO}0"' in html
    assert "data:image/jpeg" not in html


def test_residencial_renderizar_html_segue_autocontido():
    ctx = {"fotos": [{"numero": 1, "storage_key": "f/1.jpg"}]}
    html = residencial.renderizar_html(ctx, {"f/1.jpg": _jpeg()})
    assert "data:image/jpeg;base64," in html
    assert ESQUEMA_FOTO not in html


def test_foto_ausente_continua_levantando_keyerror_com_registro():
    with pytest.raises(KeyError):
        residencial._renderizar({"fotos": [{"numero": 1, "storage_key": "x"}]}, {}, RegistroDeFotos())
    with pytest.raises(KeyError):
        cautelar._renderizar({"figuras": [{"numero": 1, "storage_key": "x"}]}, {}, RegistroDeFotos())
