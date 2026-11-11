"""Testes do pipeline de renderização do RFIP (BL-12, ADR-13/DEC-25, DEC-33, DEC-36).

Usam apenas dados sintéticos e os templates versionados em `templates/rfip/`;
não dependem de `01_output-context/` nem do PostgreSQL. Os testes de contexto,
HTML e DOCX rodam em qualquer máquina; o de PDF só roda onde o WeasyPrint
carrega (container de `05_infra/`).
"""
from __future__ import annotations

import copy
import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from app.services.report_generator import rfip_pipeline


def _jpeg(cor: tuple[int, int, int], tamanho: tuple[int, int] = (64, 48)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", tamanho, cor).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def fotos_bytes() -> dict[str, bytes]:
    return {
        "fotos/1.jpg": _jpeg((200, 30, 30)),
        "fotos/2.jpg": _jpeg((30, 200, 30), (200, 40)),
        "fotos/3.jpg": _jpeg((30, 30, 200)),
    }


@pytest.fixture
def contexto() -> dict:
    """RFIP sintético: 2 sistemas fora de ordem, 4 ocorrências (uma sem foto)."""
    return {
        "responsavel": {
            "nome": "Eng. Fulana Sintética",
            "titulo_profissional": "Engenheira Civil",
            "crea": "0000000000/D-XX",
            "email": "fulana@exemplo.invalid",
            "telefone": "(00) 00000-0000",
        },
        "incluir_resumo": True,
        "ocorrencias": [
            {
                "seq_numero": 3,
                "sistema": "Instalações Hidráulicas",
                "sistema_ordem": 2,
                "subsistema": "Reservatórios",
                "subsistema_ordem": 1,
                "situacao": "Não conforme",
                "classificacao": "Anomalia",
                "tipo_anomalia": "Endógena",
                "grau_risco": "MEDIO",
                "gut_gravidade": 3.0,
                "gut_urgencia": 2.0,
                "gut_tendencia": 2.0,
                "localizacao": "Cobertura",
                "descricao": "Fissura & infiltração <tampa>",
                "fotos": [{"storage_key": "fotos/3.jpg"}],
            },
            {
                "seq_numero": 2,
                "sistema": "Estrutura",
                "sistema_ordem": 1,
                "subsistema": "Vigas",
                "subsistema_ordem": 2,
                "situacao": "Não conforme",
                "classificacao": "Falha",
                "tipo_falha": "Manutenção",
                "grau_risco": "CRITICO",
                "gut_gravidade": 5.0,
                "gut_urgencia": 5.0,
                "gut_tendencia": 4.0,
                "localizacao": "Garagem",
                "descricao": "Armadura exposta",
                "fotos": [{"storage_key": "fotos/2.jpg"}],
            },
            {
                "seq_numero": 1,
                "sistema": "Estrutura",
                "sistema_ordem": 1,
                "subsistema": "Pilares",
                "subsistema_ordem": 1,
                "classificacao": "Anomalia",
                "fotos": [{"storage_key": "fotos/1.jpg"}],
            },
            {
                "seq_numero": 4,
                "sistema": "Estrutura",
                "sistema_ordem": 1,
                "subsistema": "Pilares",
                "subsistema_ordem": 1,
                "descricao": "Sem foto",
            },
        ],
    }


# --- contexto ---------------------------------------------------------------


def test_normalizar_contexto_agrupa_ordena_e_nao_muta(contexto: dict) -> None:
    original = copy.deepcopy(contexto)
    normalizado = rfip_pipeline.normalizar_contexto(contexto)

    assert contexto == original
    assert [s["nome"] for s in normalizado["sistemas"]] == ["Estrutura", "Instalações Hidráulicas"]
    estrutura = normalizado["sistemas"][0]["ocorrencias"]
    # RN-11: Subsistema (ordem do gabarito) e depois nº da foto.
    assert [o["seq_numero"] for o in estrutura] == [1, 4, 2]
    assert normalizado["incluir_resumo"] is True


def test_campos_vazios_viram_traco(contexto: dict) -> None:
    contexto["responsavel"] = {"nome": "  ", "crea": None}
    contexto["incluir_resumo"] = None
    normalizado = rfip_pipeline.normalizar_contexto(contexto)

    for chave in ("nome", "titulo_profissional", "crea", "email", "telefone"):
        assert normalizado["responsavel"][chave] == rfip_pipeline.VAZIO
    assert normalizado["incluir_resumo"] is False

    por_numero = {o["seq_numero"]: o for s in normalizado["sistemas"] for o in s["ocorrencias"]}
    assert por_numero[1]["pontuacao_gut"] == rfip_pipeline.VAZIO
    assert por_numero[1]["localizacao"] == rfip_pipeline.VAZIO
    assert por_numero[1]["tipo_falha"] == rfip_pipeline.VAZIO
    assert por_numero[2]["pontuacao_gut"] == 100
    assert por_numero[3]["gut_gravidade"] == 3  # Float inteiro sai sem ".0"


def test_sistemas_ja_agrupados_e_nome_vazio(contexto: dict) -> None:
    contexto = {"sistemas": [{"nome": "", "ocorrencias": [{"seq_numero": 1}]}]}
    normalizado = rfip_pipeline.normalizar_contexto(contexto)
    assert normalizado["sistemas"][0]["nome"] == rfip_pipeline.VAZIO


def test_ocorrencia_sem_sistema_falha(contexto: dict) -> None:
    contexto["ocorrencias"][0].pop("sistema")
    with pytest.raises(ValueError, match="RN-11"):
        rfip_pipeline.normalizar_contexto(contexto)


# --- HTML -------------------------------------------------------------------


def test_html_com_fichas_fotos_e_escape(contexto: dict, fotos_bytes: dict[str, bytes]) -> None:
    html = rfip_pipeline.renderizar_html(contexto, fotos_bytes)

    assert "7.1. Estrutura" in html
    assert "7.2. Instalações Hidráulicas" in html
    for numero in (1, 2, 3, 4):
        assert f"Foto nº {numero:02d}" in html
    assert html.count("data:image/jpeg;base64,") == 3  # a 4ª ocorrência não tem foto
    assert "Eng. Fulana Sintética" in html and "CREA nº 0000000000/D-XX" in html
    # Autoescape: o que o engenheiro digita não vira marcação.
    assert "Fissura &amp; infiltração &lt;tampa&gt;" in html
    assert "<tampa>" not in html
    # Sem variável de página: a numeração é do formato (counter(page)).
    assert "counter(page)" in html
    assert "{{" not in html and "{%" not in html


def test_html_quadro_resumo_e_opcional(contexto: dict, fotos_bytes: dict[str, bytes]) -> None:
    com = rfip_pipeline.renderizar_html(contexto, fotos_bytes)
    contexto["incluir_resumo"] = False
    sem = rfip_pipeline.renderizar_html(contexto, fotos_bytes)

    assert 'class="resumo"' in com
    assert "OBSERVAÇÕES TÉCNICAS" in com
    assert 'class="resumo"' not in sem
    # O resumo repete uma linha por ocorrência: 4 fichas + 4 linhas.
    assert com.count("Foto nº 02") == sem.count("Foto nº 02") + 1


def test_html_vazio_sai_como_traco(fotos_bytes: dict[str, bytes]) -> None:
    html = rfip_pipeline.renderizar_html({"ocorrencias": [{"seq_numero": 1, "sistema": "Estrutura"}]}, fotos_bytes)
    assert ">—<" in html


def test_foto_ausente_levanta_keyerror(contexto: dict, fotos_bytes: dict[str, bytes]) -> None:
    del fotos_bytes["fotos/2.jpg"]
    with pytest.raises(KeyError, match=r"fotos/2.jpg"):
        rfip_pipeline.renderizar_html(contexto, fotos_bytes)


# --- DOCX -------------------------------------------------------------------


def _texto_docx(caminho: Path) -> str:
    from docx import Document

    documento = Document(str(caminho))
    partes = [p.text for p in documento.paragraphs]
    for tabela in documento.tables:
        for linha in tabela.rows:
            partes.extend(celula.text for celula in linha.cells)
    return "\n".join(partes)


def test_docx_gerado_com_fotos(contexto: dict, fotos_bytes: dict[str, bytes], tmp_path: Path) -> None:
    destino = tmp_path / "rfip.docx"
    metricas = rfip_pipeline.gerar_docx(contexto, fotos_bytes, destino)

    assert set(metricas) == {"montagem_fotos", "render_e_salvar", "total", "tamanho_bytes"}
    assert metricas["tamanho_bytes"] == destino.stat().st_size
    texto = _texto_docx(destino)
    for numero in (1, 2, 3, 4):
        assert f"Foto nº {numero:02d}" in texto
    assert "7.1. Estrutura" in texto
    assert "Fissura & infiltração <tampa>" in texto  # autoescape: texto literal, XML íntegro
    assert "{{" not in texto and "{%" not in texto

    with zipfile.ZipFile(destino) as pacote:
        midias = [n for n in pacote.namelist() if n.startswith("word/media/")]
        rodape = pacote.read("word/footer1.xml").decode("utf-8")
    # 3 fotos das fichas + a logo do cabeçalho.
    assert len(midias) == 4
    assert "PAGE" in rodape  # DEC-36 B: numeração pelo campo do Word, a partir de 1


def test_docx_foto_cabe_na_caixa_sem_deformar(fotos_bytes: dict[str, bytes], tmp_path: Path) -> None:
    from docx import Document

    contexto = {"ocorrencias": [{"seq_numero": 2, "sistema": "Estrutura", "fotos": [{"storage_key": "fotos/2.jpg"}]}]}
    destino = tmp_path / "rfip.docx"
    rfip_pipeline.gerar_docx(contexto, fotos_bytes, destino)

    larguras = [forma.width for forma in Document(str(destino)).inline_shapes]
    alturas = [forma.height for forma in Document(str(destino)).inline_shapes]
    caixa_largura_mm, _ = rfip_pipeline._caixa_foto_mm()
    # Foto 200x40 (5:1): limitada pela largura da caixa, proporção preservada.
    assert max(larguras) / 36000 == pytest.approx(caixa_largura_mm, abs=0.5)
    idx = larguras.index(max(larguras))
    assert larguras[idx] / alturas[idx] == pytest.approx(5.0, rel=0.02)


def test_docx_foto_ausente_levanta_keyerror(contexto: dict, fotos_bytes: dict[str, bytes], tmp_path: Path) -> None:
    del fotos_bytes["fotos/3.jpg"]
    with pytest.raises(KeyError, match=r"fotos/3.jpg"):
        rfip_pipeline.gerar_docx(contexto, fotos_bytes, tmp_path / "x.docx")


def test_docx_aceita_template_alternativo(contexto: dict, fotos_bytes: dict[str, bytes], tmp_path: Path) -> None:
    destino = tmp_path / "rfip.docx"
    template = rfip_pipeline.TEMPLATES_DIR / rfip_pipeline.DOCX_TEMPLATE_NAME
    rfip_pipeline.gerar_docx(contexto, fotos_bytes, destino, template_path=template)
    assert destino.stat().st_size > 0


# --- PDF --------------------------------------------------------------------


def _exigir_weasyprint() -> None:
    try:
        import weasyprint  # noqa: F401
    except (ImportError, OSError) as erro:
        pytest.skip(
            "WeasyPrint indisponível nesta máquina "
            f"({type(erro).__name__}): só carrega no container de 05_infra (GTK/Pango ausentes no Windows)."
        )


def test_pdf_gerado_com_weasyprint(contexto: dict, fotos_bytes: dict[str, bytes], tmp_path: Path) -> None:
    _exigir_weasyprint()
    destino = tmp_path / "rfip.pdf"
    metricas = rfip_pipeline.gerar_pdf(contexto, fotos_bytes, destino)

    assert destino.read_bytes().startswith(b"%PDF")
    assert metricas["tamanho_bytes"] == destino.stat().st_size
    assert metricas["n_paginas"] >= 2  # fichas (2 por página) + quadro-resumo
    assert {"render_html", "conversao_pdf", "total", "n_paginas", "tamanho_bytes"} <= set(metricas)
