"""Testes do pipeline de renderização do LTIP (BL-17, ADR-13/DEC-25, RF-06, RN-11).

Usam apenas dados sintéticos e os templates versionados em `templates/ltip/`;
não dependem de `01_output-context/` nem do PostgreSQL. Os testes de contexto,
HTML e DOCX rodam em qualquer máquina; o de PDF só roda onde o WeasyPrint
carrega (container de `05_infra/`).
"""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from app.services.report_generator import ltip_pipeline


def _jpeg(cor: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), cor).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def fotos_bytes() -> dict[str, bytes]:
    return {
        "fotos/1.jpg": _jpeg((200, 30, 30)),
        "fotos/2.jpg": _jpeg((30, 200, 30)),
        "fotos/3.jpg": _jpeg((30, 30, 200)),
    }


@pytest.fixture
def contexto() -> dict:
    """Laudo sintético: 2 sistemas fora de ordem, 4 ocorrências (uma sem foto)."""
    return {
        "edificacao": {"nome": "Residencial Sintético"},
        "fiscal": {"nome": "Eng. Fulano de Tal", "crea": "1234567890/D-GO"},
        "contrato": {"art_fiscalizacao": "ART-0001"},
        "data_emissao": "2026-11-04",
        "introducao": "Primeiro parágrafo da introdução.\n\nSegundo parágrafo.",
        "metodologia_paragrafos": ["Metodologia NBR 16747."],
        "conclusao": "Conclusão do laudo.",
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
                "prioridade": 3,
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
                "prioridade": 5,
                "gut_gravidade": 5.0,
                "gut_urgencia": 5.0,
                "gut_tendencia": 4.0,
                "localizacao": "Garagem",
                "descricao": "Armadura exposta.",
                "fotos": [{"storage_key": "fotos/2.jpg"}],
            },
            {
                "seq_numero": 1,
                "sistema": "Estrutura",
                "sistema_ordem": 1,
                "subsistema": "Pilares",
                "subsistema_ordem": 1,
                "situacao": "Conforme",
                "classificacao": "Conforme",
                "grau_risco": "MINIMO",
                "prioridade": 0,
                "fotos": [{"storage_key": "fotos/1.jpg"}],
            },
            {
                "seq_numero": 4,
                "sistema": "Estrutura",
                "sistema_ordem": 1,
                "subsistema": "Vigas",
                "subsistema_ordem": 2,
                "situacao": "Não conforme",
                "classificacao": "Anomalia",
                "grau_risco": "MINIMO",
                "prioridade": 1,
                "fotos": [],
            },
        ],
    }


# --- contexto ---------------------------------------------------------------


def test_contexto_agrupa_por_sistema_e_subsistema_rn11(contexto: dict) -> None:
    normalizado = ltip_pipeline.normalizar_contexto(contexto)
    assert [s["nome"] for s in normalizado["sistemas"]] == ["Estrutura", "Instalações Hidráulicas"]
    estrutura = normalizado["sistemas"][0]["ocorrencias"]
    # Pilares (ordem 1) antes de Vigas (ordem 2); dentro de Vigas, pelo nº da foto.
    assert [o["seq_numero"] for o in estrutura] == [1, 2, 4]


def test_contexto_sem_ordem_preserva_primeira_aparicao(contexto: dict) -> None:
    for ocorrencia in contexto["ocorrencias"]:
        ocorrencia.pop("sistema_ordem")
    normalizado = ltip_pipeline.normalizar_contexto(contexto)
    assert [s["nome"] for s in normalizado["sistemas"]] == ["Instalações Hidráulicas", "Estrutura"]


def test_contexto_aceita_sistemas_ja_agrupados(contexto: dict) -> None:
    sistemas = ltip_pipeline.agrupar_por_sistema(contexto.pop("ocorrencias"))
    normalizado = ltip_pipeline.normalizar_contexto({**contexto, "sistemas": sistemas})
    assert [s["nome"] for s in normalizado["sistemas"]] == ["Estrutura", "Instalações Hidráulicas"]


def test_contexto_preenche_secoes_de_texto_e_emissao(contexto: dict) -> None:
    normalizado = ltip_pipeline.normalizar_contexto(contexto)
    assert normalizado["introducao_paragrafos"] == ["Primeiro parágrafo da introdução.", "Segundo parágrafo."]
    assert normalizado["metodologia_paragrafos"] == ["Metodologia NBR 16747."]
    assert normalizado["conclusao_paragrafos"] == ["Conclusão do laudo."]
    for chave in ltip_pipeline.SECOES_TEXTO:
        assert isinstance(normalizado[f"{chave}_paragrafos"], list)
    from datetime import date

    assert ltip_pipeline.normalizar_contexto({**contexto, "data_emissao": date(2026, 11, 4)})[
        "data_emissao"
    ] == "04/11/2026"


def test_contexto_calcula_gut_e_preenche_vazios(contexto: dict) -> None:
    normalizado = ltip_pipeline.normalizar_contexto(contexto)
    por_numero = {o["seq_numero"]: o for s in normalizado["sistemas"] for o in s["ocorrencias"]}
    assert por_numero[2]["pontuacao_gut"] == 100
    assert por_numero[2]["gut_gravidade"] == 5  # Float inteiro sai sem ".0"
    assert por_numero[3]["pontuacao_gut"] == 12
    assert por_numero[1]["pontuacao_gut"] == ltip_pipeline.VAZIO
    assert por_numero[1]["prioridade"] == 0  # Prioridade 0 = não aplicável, não é vazio
    assert por_numero[1]["tipo_falha"] == ltip_pipeline.VAZIO
    assert por_numero[2]["tipo_falha"] == "Manutenção"
    assert por_numero[3]["tipo_anomalia"] == "Endógena"


def test_contexto_nao_muta_a_entrada(contexto: dict) -> None:
    ltip_pipeline.normalizar_contexto(contexto)
    assert "sistemas" not in contexto
    assert contexto["ocorrencias"][0]["gut_gravidade"] == 3.0


def test_ocorrencia_sem_sistema_falha_explicitamente(contexto: dict) -> None:
    contexto["ocorrencias"][0]["sistema"] = None
    with pytest.raises(ValueError, match="sem sistema predial"):
        ltip_pipeline.normalizar_contexto(contexto)


# --- HTML -------------------------------------------------------------------


def test_html_renderiza_capa_fichas_e_fotos(contexto: dict, fotos_bytes: dict[str, bytes]) -> None:
    html = ltip_pipeline.renderizar_html(contexto, fotos_bytes)
    assert "LAUDO TÉCNICO DE INSPEÇÃO PREDIAL — Residencial Sintético" in html
    assert "Eng. Fulano de Tal" in html and "CREA nº 1234567890/D-GO" in html
    assert "ART nº ART-0001" in html
    assert "7.1. Estrutura" in html and "7.2. Instalações Hidráulicas" in html
    assert html.index("7.1. Estrutura") < html.index("7.2. Instalações Hidráulicas")
    assert html.count('class="ficha"') == 4
    assert html.count("data:image/jpeg;base64,") == 3  # a ocorrência nº 04 não tem foto
    assert "Foto nº 01" in html and "Foto nº 04" in html
    assert "Primeiro parágrafo da introdução." in html
    # Autoescape: texto do engenheiro não vira marcação.
    assert "Fissura &amp; infiltração &lt;tampa&gt;" in html
    assert "None" not in html


def test_html_agrupa_fichas_em_linhas_de_duas(contexto: dict, fotos_bytes: dict[str, bytes]) -> None:
    """T20/DEC-40: uma tabela fixa por linha de 2 fichas, não um flex único por sistema."""
    html = ltip_pipeline.renderizar_html(contexto, fotos_bytes)
    # Estrutura: [01, 02], [04]; Instalações Hidráulicas: [03].
    assert html.count('<table class="fichas">') == 3
    assert html.count('class="ficha-vazia"') == 2  # a linha incompleta mantém a largura da ficha
    assert "display: flex" not in html
    primeira_linha = html.split('<table class="fichas">')[1].split("</tr></table>")[0]
    assert primeira_linha.index("Foto nº 01") < primeira_linha.index("Foto nº 02")  # RN-11
    assert "Foto nº 04" not in primeira_linha


def test_html_do_pdf_serve_as_fotos_da_memoria(contexto: dict, fotos_bytes: dict[str, bytes]) -> None:
    """T20: no PDF as fotos vão por `url_fetcher`, sem base64 no HTML."""
    fotos_em_memoria: list[bytes] = []
    html = ltip_pipeline._renderizar(contexto, fotos_bytes, fotos_em_memoria)
    assert "data:image/jpeg" not in html
    assert html.count(f'src="{ltip_pipeline.ESQUEMA_FOTO}') == 3
    assert len(fotos_em_memoria) == 3
    ficha_01 = html[html.index("Foto nº 01"):]
    indice = int(ficha_01.split(f'src="{ltip_pipeline.ESQUEMA_FOTO}')[1].split('"')[0])
    assert fotos_em_memoria[indice] == fotos_bytes["fotos/1.jpg"]


def test_foto_referenciada_sem_bytes_falha(contexto: dict, fotos_bytes: dict[str, bytes]) -> None:
    del fotos_bytes["fotos/2.jpg"]
    with pytest.raises(KeyError, match=r"fotos/2\.jpg"):
        ltip_pipeline.renderizar_html(contexto, fotos_bytes)


# --- DOCX -------------------------------------------------------------------


def _texto_docx(caminho: Path) -> str:
    from docx import Document

    documento = Document(str(caminho))
    partes = [p.text for p in documento.paragraphs]
    for tabela in documento.tables:
        for linha in tabela.rows:
            partes.extend(celula.text for celula in linha.cells)
    return "\n".join(partes)


def test_docx_renderiza_template_versionado(
    contexto: dict, fotos_bytes: dict[str, bytes], tmp_path: Path
) -> None:
    destino = tmp_path / "ltip.docx"
    metricas = ltip_pipeline.gerar_docx(contexto, fotos_bytes, destino)

    assert destino.is_file() and metricas["tamanho_bytes"] == destino.stat().st_size
    assert set(metricas) == {"montagem_fotos", "render_e_salvar", "total", "tamanho_bytes"}
    texto = _texto_docx(destino)
    assert "{{" not in texto and "{%" not in texto
    assert "Autor: Eng. Fulano de Tal — CREA nº 1234567890/D-GO — 2026-11-04" in texto
    assert "Estrutura" in texto and "Instalações Hidráulicas" in texto
    assert texto.index("Estrutura") < texto.index("Instalações Hidráulicas")
    for numero in (1, 2, 3, 4):
        assert f"Foto nº {numero:02d}" in texto
    assert "Fissura & infiltração <tampa>" in texto  # escapado no XML, legível no Word
    assert "Manutenção" in texto and "CRITICO" in texto
    assert "None" not in texto
    assert "Eng. Fulano de Tal — CREA nº 1234567890/D-GO — ART nº ART-0001" in texto


def test_docx_embute_foto_quando_o_template_tem_o_placeholder(
    contexto: dict, fotos_bytes: dict[str, bytes], tmp_path: Path
) -> None:
    """Contrato para quando o gerador do template incluir `{{ ocorrencia.foto }}`."""
    from docx import Document

    template = tmp_path / "com_foto.docx"
    documento = Document()
    for linha in (
        "{%p for sistema in sistemas %}",
        "{%p for ocorrencia in sistema.ocorrencias %}",
        "{{ ocorrencia.foto }}",
        "{%p endfor %}",
        "{%p endfor %}",
    ):
        documento.add_paragraph(linha)
    documento.save(str(template))

    destino = tmp_path / "ltip_com_foto.docx"
    ltip_pipeline.gerar_docx(contexto, fotos_bytes, destino, template_path=template)

    imagens = [rel for rel in Document(str(destino)).part.rels.values() if "image" in rel.reltype]
    assert len(imagens) == 3


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
    destino = tmp_path / "ltip.pdf"
    metricas = ltip_pipeline.gerar_pdf(contexto, fotos_bytes, destino)

    assert destino.read_bytes().startswith(b"%PDF")
    assert metricas["tamanho_bytes"] == destino.stat().st_size
    # Capa + 6 capítulos + introdução do relatório + 2 sistemas + conclusão.
    assert metricas["n_paginas"] >= 11

    import pdfplumber

    with pdfplumber.open(destino) as pdf:
        fotos = [(numero, img) for numero, pagina in enumerate(pdf.pages[1:], 2) for img in pagina.images]
    assert len(fotos) == 3  # as 3 fotos chegaram pelo fetcher em memória; nenhuma se perdeu
    (pagina_01, foto_01), (pagina_02, foto_02) = fotos[0], fotos[1]
    # Fichas 01 e 02 lado a lado na mesma linha, com a mesma largura (2 por linha).
    assert pagina_01 == pagina_02 and abs(foto_01["top"] - foto_02["top"]) < 0.5
    assert foto_01["x0"] < foto_02["x0"] and abs(foto_01["width"] - foto_02["width"]) < 0.5


def test_fetcher_entrega_a_foto_da_memoria() -> None:
    _exigir_weasyprint()
    fotos = [_jpeg((10, 20, 30))]
    fetcher = ltip_pipeline._fetcher_de_fotos(fotos)
    if fetcher is None:
        pytest.skip("WeasyPrint sem a classe URLFetcher: o PDF usa data URI.")
    resposta = fetcher.fetch(f"{ltip_pipeline.ESQUEMA_FOTO}0")
    assert resposta.read() == fotos[0]
    assert resposta.content_type == "image/jpeg"
