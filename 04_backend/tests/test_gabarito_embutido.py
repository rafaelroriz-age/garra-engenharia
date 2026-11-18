"""Gabarito embutido (DEC-51): equivalência Markdown vs JSON, fallback e determinismo."""
import json

import pytest

from app.scripts import rfo_gabarito_parser as parser
from app.scripts.exportar_gabarito_embutido import exportar

pytestmark = pytest.mark.skipif(
    not parser.RFO_INSPECAO_MD.exists(), reason="Markdown do gabarito indisponível"
)


def test_json_embutido_equivale_ao_markdown():
    embutido = json.loads(parser.GABARITO_EMBUTIDO_JSON.read_text(encoding="utf-8"))
    assert embutido == parser.build_gabarito_from_markdown()


def test_fallback_usa_json_quando_markdown_ausente(monkeypatch, tmp_path):
    esperado = parser.build_gabarito_from_markdown()
    monkeypatch.setattr(parser, "RFO_INSPECAO_MD", tmp_path / "inexistente.md")
    assert parser.build_gabarito() == esperado


def test_sem_markdown_nem_json_levanta(monkeypatch, tmp_path):
    monkeypatch.setattr(parser, "RFO_INSPECAO_MD", tmp_path / "x.md")
    monkeypatch.setattr(parser, "GABARITO_EMBUTIDO_JSON", tmp_path / "x.json")
    with pytest.raises(FileNotFoundError):
        parser.build_gabarito()


def test_exportador_deterministico(tmp_path):
    a = exportar(tmp_path / "a.json")
    b = exportar(tmp_path / "b.json")
    assert a.read_bytes() == b.read_bytes()
    assert a.read_bytes() == parser.GABARITO_EMBUTIDO_JSON.read_bytes()
