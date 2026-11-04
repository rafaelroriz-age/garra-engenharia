"""Testes do pipeline de renderização da Vistoria Cautelar (DEC-35, ADR-13).

Usam só dados sintéticos e os templates versionados em
`templates/vistoria_cautelar/`; não dependem de `01_output-context/` nem do
PostgreSQL. HTML e DOCX rodam em qualquer máquina; o PDF só onde o WeasyPrint
carrega (container de `05_infra/`).
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from app.services.report_generator import vistoria_cautelar_pipeline as pipeline


def _jpeg(cor: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), cor).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def fotos_bytes() -> dict[str, bytes]:
    return {
        "fotos/1.jpg": _jpeg((200, 30, 30)),
        "fotos/2.jpg": _jpeg((30, 200, 30)),
        "assinatura.jpg": _jpeg((10, 10, 10)),
    }


@pytest.fixture
def contexto() -> dict:
    return {
        "responsavel": {
            "nome": "Eng. Fulano & Cia <Sintético>",
            "titulo_profissional": "Engenheiro Civil",
            "crea": "0000000000/D-XX",
            "email": "fulano@example.com",
            "telefone": "(00) 00000-0000",
            "qualificacoes": ["Pós-graduado em Patologia das Construções"],
        },
        "obra": {"descricao": "Reforma do Bloco Sintético"},
        "edificacao": {"nome": "Condomínio Sintético"},
        "data_emissao": "2026-11-04",
        "local_emissao": "Cidade Sintética",
        "conteudo": {
            "introducao": "Primeiro parágrafo.\n\nSegundo parágrafo & fim.",
            "metodologia": ["Metodologia NBR 16747."],
            "encerramento": ["Encerramento do laudo."],
        },
        "complementos": {"parecer_tecnico": "Recebimento com ressalvas"},
        "tabelas": {
            "identificacao": [{"aspecto_tecnico": "Endereço", "descricao_detalhada": "Rua Sintética, 1"}],
            "plano_de_correcoes_remanescentes": [
                {
                    "item": "1",
                    "localizacao": "Garagem",
                    "descricao_da_pendencia": "Trinca <fina>",
                    "metodologia_corretiva_indicada": "",
                }
            ],
        },
        "sistemas": [
            {"nome": "Revestimentos", "constatacoes": "Constatação A.\nConstatação B.", "fundamentacao_tecnica": ["NBR 13749."]},
            {"nome": "Instalações Hidráulicas", "constatacoes": ["Constatação C."], "fundamentacao_tecnica": []},
        ],
        "figuras": [
            {"legenda": "Fachada norte.", "storage_key": "fotos/1.jpg"},
            {"numero": 7, "legenda": "", "storage_key": "fotos/2.jpg"},
        ],
        "assinatura_storage_key": "assinatura.jpg",
    }


def _texto_docx(caminho: Path) -> str:
    from docx import Document

    doc = Document(str(caminho))
    partes = [p.text for p in doc.paragraphs]
    for tabela in doc.tables:
        for linha in tabela.rows:
            partes.extend(celula.text for celula in linha.cells)
    for secao in doc.sections:
        partes.extend(p.text for p in secao.footer.paragraphs)
    return "\n".join(partes)


def test_normalizar_nao_muta_e_aplica_defaults(contexto):
    original = {"responsavel": {"nome": ""}, "data_emissao": "2026-11-04"}
    ctx = pipeline.normalizar_contexto(original)
    assert original == {"responsavel": {"nome": ""}, "data_emissao": "2026-11-04"}
    assert ctx["responsavel"]["nome"] == pipeline.VAZIO
    assert ctx["responsavel"]["crea"] == pipeline.VAZIO
    assert ctx["obra"]["descricao"] == pipeline.VAZIO
    assert ctx["edificacao"]["nome"] == pipeline.VAZIO
    assert ctx["local_emissao"] == pipeline.VAZIO
    assert ctx["data_emissao_mes_ano"] == "Novembro de 2026"
    assert ctx["data_emissao_extenso"] == "4 de novembro de 2026"
    assert ctx["conteudo"] == {} and ctx["sistemas"] == [] and ctx["figuras"] == []


def test_normalizar_paragrafos_numeracao_e_celulas_vazias(contexto):
    ctx = pipeline.normalizar_contexto(contexto)
    assert ctx["conteudo"]["introducao"] == ["Primeiro parágrafo.", "Segundo parágrafo & fim."]
    assert ctx["sistemas"][0]["constatacoes"] == ["Constatação A.", "Constatação B."]
    assert [f["numero"] for f in ctx["figuras"]] == [1, 7]
    assert ctx["figuras"][1]["legenda"] == pipeline.VAZIO
    assert ctx["tabelas"]["plano_de_correcoes_remanescentes"][0]["metodologia_corretiva_indicada"] == pipeline.VAZIO


def test_html_renderiza_contexto_com_autoescape_e_fotos(contexto, fotos_bytes):
    html = pipeline.renderizar_html(contexto, fotos_bytes)
    assert "Eng. Fulano &amp; Cia &lt;Sintético&gt;" in html
    assert "Eng. Fulano & Cia <Sintético>" not in html
    assert "Condomínio Sintético" in html
    assert "Segundo parágrafo &amp; fim." in html
    assert "9.1. Revestimentos" in html and "9.2. Instalações Hidráulicas" in html
    assert "9.3. Correlação Técnica" in html
    assert "Recebimento com ressalvas" in html
    assert "Figura 7 - — Fonte: Autor." in html
    assert "Trinca &lt;fina&gt;" in html
    assert "4 de novembro de 2026" in html
    assert html.count("data:image/jpeg;base64,") >= 3  # 2 figuras + assinatura
    assert "{{" not in html and "{%" not in html


def test_html_foto_ausente_levanta_keyerror(contexto, fotos_bytes):
    del fotos_bytes["fotos/2.jpg"]
    with pytest.raises(KeyError, match="fotos/2.jpg"):
        pipeline.renderizar_html(contexto, fotos_bytes)


def test_html_sem_figuras_nem_sistemas_com_campos_vazios():
    html = pipeline.renderizar_html({"data_emissao": "2026-01-02"}, {})
    assert "{{" not in html and "{%" not in html
    assert pipeline.VAZIO in html
    # Sem sistemas, a subseção fixa de correlação técnica assume o 9.1.
    assert "9.1. Correlação Técnica" in html and "9.2." not in html


def test_docx_gera_arquivo_com_texto_e_metricas(contexto, fotos_bytes, tmp_path):
    destino = tmp_path / "vistoria.docx"
    metricas = pipeline.gerar_docx(contexto, fotos_bytes, destino)
    assert set(metricas) == {"montagem_fotos", "render_e_salvar", "total", "tamanho_bytes"}
    assert metricas["tamanho_bytes"] == destino.stat().st_size > 0
    texto = _texto_docx(destino)
    assert "Eng. Fulano & Cia <Sintético>" in texto
    assert "Condomínio Sintético" in texto
    assert "Constatação C." in texto
    assert "Trinca <fina>" in texto
    assert "{{" not in texto and "{%" not in texto
    with zipfile.ZipFile(destino) as z:
        midias = [n for n in z.namelist() if n.startswith("word/media/")]
        assert len([n for n in midias if n.endswith((".jpg", ".jpeg"))]) >= 3  # 2 figuras + assinatura


def test_docx_foto_ausente_levanta_keyerror(contexto, fotos_bytes, tmp_path):
    del fotos_bytes["fotos/1.jpg"]
    with pytest.raises(KeyError, match="fotos/1.jpg"):
        pipeline.gerar_docx(contexto, fotos_bytes, tmp_path / "x.docx")


def test_docx_sem_figuras_e_com_template_alternativo(tmp_path):
    destino = tmp_path / "vazio.docx"
    template = pipeline.TEMPLATES_DIR / pipeline.DOCX_TEMPLATE_NAME
    pipeline.gerar_docx({"data_emissao": "2026-01-02"}, {}, destino, template_path=template)
    assert pipeline.VAZIO in _texto_docx(destino)


def test_pdf_gera_arquivo_e_metricas(contexto, fotos_bytes, tmp_path):
    try:
        import weasyprint  # noqa: F401
    except (ImportError, OSError) as exc:
        pytest.skip(f"WeasyPrint indisponível neste ambiente: {exc.__class__.__name__}")
    destino = tmp_path / "vistoria.pdf"
    metricas = pipeline.gerar_pdf(contexto, fotos_bytes, destino)
    assert set(metricas) == {"render_html", "conversao_pdf", "total", "n_paginas", "tamanho_bytes"}
    assert metricas["n_paginas"] >= 3
    assert destino.read_bytes().startswith(b"%PDF")
