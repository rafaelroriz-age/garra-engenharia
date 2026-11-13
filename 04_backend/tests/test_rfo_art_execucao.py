"""RFO: ART de Execução ausente imprime '—' no HTML e no DOCX (DEC-33, DEC-47).

Não dependem de banco nem do WeasyPrint: `rfo_contexto` é carregado com um pacote
`app.services.report_generator` vazio (o `__init__` real importa o WeasyPrint, que
não carrega no Windows local). O HTML é renderizado com o template real via Jinja e
o DOCX com o template real via docxtpl; nenhum PDF é gerado.
"""

from __future__ import annotations

import io
import re
import sys
import types
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from docxtpl import DocxTemplate
from jinja2 import ChainableUndefined, Environment, FileSystemLoader, select_autoescape

_BACKEND = Path(__file__).resolve().parents[1]
_PACOTE = _BACKEND / "app" / "services" / "report_generator"

if "app.services.report_generator" not in sys.modules:
    _stub = types.ModuleType("app.services.report_generator")
    _stub.__path__ = [str(_PACOTE)]
    sys.modules["app.services.report_generator"] = _stub

from app.services.report_generator.rfo_contexto import _executor_ctx, _texto_ou_traco  # noqa: E402

TRACO = "—"


def _executor(art_execucao):
    return SimpleNamespace(
        razao_social="Executora X",
        cnpj="00.000.000/0001-00",
        endereco="Rua A, 1",
        art_execucao=art_execucao,
        responsavel_legal=None,
        rte=None,
    )


@pytest.mark.parametrize("valor", [None, "", "   ", "\n\t "])
def test_texto_ou_traco_vazio_vira_traco(valor):
    assert _texto_ou_traco(valor) == TRACO


def test_texto_ou_traco_preserva_valor_preenchido_sem_alterar_formato():
    assert _texto_ou_traco("ART-EXEC-001") == "ART-EXEC-001"
    assert _texto_ou_traco(" ART-EXEC-001 ") == " ART-EXEC-001 "


def test_executor_ctx_art_nula_vira_traco():
    ctx = _executor_ctx(_executor(None))
    assert ctx["art_execucao"] == TRACO


def test_executor_ctx_art_com_espacos_vira_traco():
    assert _executor_ctx(_executor("   "))["art_execucao"] == TRACO


def test_executor_ctx_art_preenchida_inalterada():
    assert _executor_ctx(_executor("ART-EXEC-001"))["art_execucao"] == "ART-EXEC-001"


def test_executor_ctx_demais_campos_inalterados():
    ctx = _executor_ctx(_executor(None))
    assert ctx["razao_social"] == "Executora X"
    assert ctx["cnpj"] == "00.000.000/0001-00"
    assert ctx["endereco"] == "Rua A, 1"
    assert ctx["responsavel_legal"] is None
    assert ctx["rte"] is None


def _contexto_sintetico(art_execucao):
    return {"executores": [_executor_ctx(_executor(art_execucao))], "nbrs": [], "visitas": []}


def test_html_imprime_traco_quando_art_falta():
    env = Environment(
        loader=FileSystemLoader(str(_BACKEND / "templates" / "rfo")),
        autoescape=select_autoescape(["html", "j2"]),
        undefined=ChainableUndefined,
    )
    html = env.get_template("rfo_template.html.j2").render(**_contexto_sintetico(None))
    assert "ART de Execução:</td><td>—</td>" in html
    assert "None" not in html


def test_html_imprime_art_preenchida():
    env = Environment(
        loader=FileSystemLoader(str(_BACKEND / "templates" / "rfo")),
        autoescape=select_autoescape(["html", "j2"]),
        undefined=ChainableUndefined,
    )
    html = env.get_template("rfo_template.html.j2").render(**_contexto_sintetico("ART-EXEC-001"))
    assert "ART de Execução:</td><td>ART-EXEC-001</td>" in html


def _texto_docx(contexto) -> str:
    tpl = DocxTemplate(str(_BACKEND / "templates" / "rfo" / "rfo_template.docx"))
    tpl.render(contexto, jinja_env=Environment(undefined=ChainableUndefined))
    saida = io.BytesIO()
    tpl.save(saida)
    with zipfile.ZipFile(io.BytesIO(saida.getvalue())) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    return re.sub(r"<[^>]+>", "", xml)


def test_docx_imprime_traco_quando_art_falta():
    texto = _texto_docx(_contexto_sintetico(None))
    assert f"ART de Execução: {TRACO}" in texto
    assert "None" not in texto


def test_docx_imprime_art_preenchida():
    texto = _texto_docx(_contexto_sintetico("ART-EXEC-001"))
    assert "ART-EXEC-001" in texto
