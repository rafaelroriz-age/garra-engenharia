"""Testes do pipeline de renderização da Vistoria Residencial (DEC-35, ADR-13/DEC-25).

Usam apenas dados sintéticos e os templates versionados em
`templates/vistoria_residencial/`; não dependem de `01_output-context/` nem do
PostgreSQL. HTML e DOCX rodam em qualquer máquina; o PDF só onde o WeasyPrint
carrega (container de `05_infra/`).
"""
from __future__ import annotations

import io
import re
from datetime import date
from pathlib import Path

import pytest
from PIL import Image

from app.services.report_generator import vistoria_residencial_pipeline as pipeline


def _jpeg(cor: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), cor).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def fotos_bytes() -> dict[str, bytes]:
    return {"fotos/1.jpg": _jpeg((200, 30, 30)), "fotos/2.jpg": _jpeg((30, 200, 30))}


@pytest.fixture
def contexto() -> dict:
    return {
        "imovel": {"unidade": "Ap. 101"},
        "edificacao": {"nome": "Residencial Sintético"},
        "fiscal": {
            "nome": "Fulano de Tal",
            "crea": "1234567890/D-GO",
            "email": "fulano@example.com",
            "telefone": "(62) 90000-0000",
            "qualificacoes": ["Engenheiro Civil", "Perito Judicial"],
        },
        "data_emissao": date(2026, 11, 4),
        "local_emissao": "Goiânia",
        "textos": {
            "s1": "Primeiro parágrafo da introdução.\n\nSegundo parágrafo.",
            "s4_2_1": ["Tipologia residencial multifamiliar."],
            "s10": ["Conclusão do laudo."],
        },
        "fotos": [
            {"legenda": "Fissura & infiltração <tampa>", "storage_key": "fotos/1.jpg"},
            {"numero": 7, "legenda": "", "fonte": "Cliente", "storage_key": "fotos/2.jpg"},
            {"legenda": "Sem imagem"},
        ],
        "sistemas": [
            {
                "nome": "Estrutura e Laje",
                "constatacoes": ["Fissura na laje.", "Eflorescência."],
                "fundamentacao_tecnica": ["NBR 16747 §5."],
            },
            {"nome": "Esquadrias", "constatacoes": [], "fundamentacao_tecnica": None},
        ],
    }


# --- Contexto ---------------------------------------------------------------


def test_chaves_de_textos_batem_com_os_templates() -> None:
    html = (pipeline.TEMPLATES_DIR / pipeline.HTML_TEMPLATE_NAME).read_text(encoding="utf-8")
    assert re.findall(r"textos\.(\w+)", html) == list(pipeline.TEXTOS_CHAVES)


def test_contexto_normaliza_textos_e_vazios(contexto: dict) -> None:
    c = pipeline.normalizar_contexto(contexto)
    assert c["textos"]["s1"] == ["Primeiro parágrafo da introdução.", "Segundo parágrafo."]
    assert c["textos"]["s12"] == []
    assert c["data_emissao"] == "04/11/2026"
    assert c["fotos"][0]["numero"] == 1 and c["fotos"][1]["numero"] == 7
    assert c["fotos"][1]["legenda"] == pipeline.VAZIO
    assert c["sistemas"][1]["constatacoes"] == [pipeline.VAZIO]
    assert c["sistemas"][1]["fundamentacao_tecnica"] == [pipeline.VAZIO]


def test_contexto_minimo_usa_traco_dec33() -> None:
    c = pipeline.normalizar_contexto({})
    assert c["imovel"]["unidade"] == pipeline.VAZIO
    assert c["fiscal"]["crea"] == pipeline.VAZIO
    assert c["local_emissao"] == pipeline.VAZIO
    assert c["fotos"] == [] and c["sistemas"] == []


def test_contexto_nao_muta_a_entrada(contexto: dict) -> None:
    antes = repr(contexto)
    pipeline.normalizar_contexto(contexto)
    assert repr(contexto) == antes


# --- HTML -------------------------------------------------------------------


def test_html_renderiza_capa_textos_fotos_e_sistemas(contexto: dict, fotos_bytes: dict[str, bytes]) -> None:
    html = pipeline.renderizar_html(contexto, fotos_bytes)
    assert "Ap. 101" in html and "Residencial Sintético" in html
    assert "ENG. CIVIL FULANO DE TAL" in html
    assert "Segundo parágrafo." in html and "Tipologia residencial multifamiliar." in html
    assert html.count("data:image/jpeg;base64,") == 2
    assert "Figura 7 - —. Fonte: Cliente." in html and "Fonte: Autor." in html
    assert "Fissura &amp; infiltração &lt;tampa&gt;" in html  # autoescape
    assert "9.1. Estrutura e Laje" in html and "9.2. Esquadrias" in html
    assert "Perito Judicial" in html
    assert "Goiânia, 04/11/2026." in html
    assert "None" not in html and "{{" not in html and "{%" not in html


def test_foto_referenciada_sem_bytes_falha(contexto: dict, fotos_bytes: dict[str, bytes]) -> None:
    del fotos_bytes["fotos/2.jpg"]
    with pytest.raises(KeyError, match=r"fotos/2.jpg"):
        pipeline.renderizar_html(contexto, fotos_bytes)


def test_foto_ausente_tambem_falha_no_docx(contexto: dict, fotos_bytes: dict[str, bytes], tmp_path: Path) -> None:
    del fotos_bytes["fotos/1.jpg"]
    with pytest.raises(KeyError, match=r"fotos/1.jpg"):
        pipeline.gerar_docx(contexto, fotos_bytes, tmp_path / "x.docx")


# --- DOCX -------------------------------------------------------------------


def _texto_docx(caminho: Path) -> str:
    from docx import Document

    documento = Document(str(caminho))
    partes = [p.text for p in documento.paragraphs]
    for tabela in documento.tables:
        for linha in tabela.rows:
            partes.extend(celula.text for celula in linha.cells)
    return "\n".join(partes)


def test_docx_renderiza_template_versionado(contexto: dict, fotos_bytes: dict[str, bytes], tmp_path: Path) -> None:
    from docx import Document

    destino = tmp_path / "vistoria.docx"
    metricas = pipeline.gerar_docx(contexto, fotos_bytes, destino)

    assert destino.is_file() and metricas["tamanho_bytes"] == destino.stat().st_size
    assert set(metricas) == {"montagem_fotos", "render_e_salvar", "total", "tamanho_bytes"}
    texto = _texto_docx(destino)
    assert "{{" not in texto and "{%" not in texto and "None" not in texto
    assert "Ap. 101" in texto and "Residencial Sintético" in texto
    assert "Segundo parágrafo." in texto and "Fissura na laje." in texto
    assert "Fissura & infiltração <tampa>" in texto  # escapado no XML, legível no Word
    assert "Estrutura e Laje" in texto and "Esquadrias" in texto
    imagens = [rel for rel in Document(str(destino)).part.rels.values() if "image" in rel.reltype]
    # 2 fotos + imagens fixas do template (logo etc.): ao menos as 2 fotos entram.
    assert len(imagens) >= 2


# --- PDF --------------------------------------------------------------------


def test_pdf_gerado_com_weasyprint(contexto: dict, fotos_bytes: dict[str, bytes], tmp_path: Path) -> None:
    try:
        import weasyprint  # noqa: F401
    except (ImportError, OSError) as erro:
        pytest.skip(
            f"WeasyPrint indisponível nesta máquina ({type(erro).__name__}): "
            "só carrega no container de 05_infra (GTK/Pango ausentes no Windows)."
        )
    destino = tmp_path / "vistoria.pdf"
    metricas = pipeline.gerar_pdf(contexto, fotos_bytes, destino)

    assert destino.read_bytes().startswith(b"%PDF")
    assert metricas["tamanho_bytes"] == destino.stat().st_size
    assert set(metricas) == {"render_html", "conversao_pdf", "total", "n_paginas", "tamanho_bytes"}
    assert metricas["n_paginas"] >= 12  # capa + rosto + capítulos com quebra de página
