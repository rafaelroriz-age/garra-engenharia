"""Testes do vetorizador de bitmap e dos assets de marca (B-02/RN-07).

Não dependem de `01_output-context/` nem da marca real: as formas são
sintéticas, construídas em memória. Os testes finais checam os artefatos já
versionados em `templates/assets/`, que são o que de fato entra nos
relatórios.
"""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image

from app.scripts.bitmap_tracer import (
    area,
    caminho_svg,
    extrair_contornos,
    simplificar,
    vetorizar,
)
from app.scripts.build_brand_assets import (
    MarcaError,
    detectar_fundo,
    extrair_tons,
    linha_de_corte,
    montar_png,
    montar_svg,
    recortar_conteudo,
)

ASSETS = Path(__file__).resolve().parents[1] / "templates" / "assets"
SVG_NS = "{http://www.w3.org/2000/svg}"


def _mascara(largura: int, altura: int, dentro) -> list[list[bool]]:
    return [[bool(dentro(x, y)) for x in range(largura)] for y in range(altura)]


# --- Vetorizador -------------------------------------------------------------


def test_quadrado_gera_um_contorno_com_area_do_quadrado():
    mascara = _mascara(10, 10, lambda x, y: 2 <= x < 7 and 3 <= y < 8)

    contornos = extrair_contornos(mascara)

    assert len(contornos) == 1
    assert abs(area(contornos[0])) == pytest.approx(25.0)


def test_quadrado_com_furo_gera_contornos_de_sentidos_opostos():
    mascara = _mascara(12, 12, lambda x, y: 1 <= x < 11 and 1 <= y < 11 and not (4 <= x < 7 and 4 <= y < 7))

    contornos = extrair_contornos(mascara)

    assert len(contornos) == 2
    externo, furo = sorted(contornos, key=lambda c: abs(area(c)), reverse=True)
    assert abs(area(externo)) == pytest.approx(100.0)
    assert abs(area(furo)) == pytest.approx(9.0)
    # Sentidos opostos: é o que permite ao `fill-rule="evenodd"` vazar o furo.
    assert area(externo) * area(furo) < 0


def test_pixels_encostados_na_diagonal_formam_um_unico_contorno():
    mascara = _mascara(6, 6, lambda x, y: (x, y) in {(1, 1), (2, 2)})

    assert len(extrair_contornos(mascara)) == 1


def test_simplificar_reduz_a_escada_do_retangulo_aos_quatro_cantos():
    mascara = _mascara(20, 10, lambda x, y: 2 <= x < 18 and 2 <= y < 8)
    contorno = extrair_contornos(mascara)[0]

    simplificado = simplificar(contorno, tolerancia=0.6)

    assert len(contorno) == 44  # o rastreamento emite um vértice por aresta de pixel
    assert len(simplificado) == 4
    assert abs(area(simplificado)) == pytest.approx(abs(area(contorno)))


def test_caminho_svg_usa_reta_em_canto_vivo_e_bezier_em_curva():
    quadrado = simplificar(extrair_contornos(_mascara(12, 12, lambda x, y: 2 <= x < 10 and 2 <= y < 10))[0], 0.6)
    circulo = simplificar(
        extrair_contornos(_mascara(80, 80, lambda x, y: (x - 40) ** 2 + (y - 40) ** 2 < 30**2))[0], 0.6
    )

    caminho_quadrado = caminho_svg(quadrado)
    caminho_circulo = caminho_svg(circulo)

    assert "Q" not in caminho_quadrado
    assert caminho_quadrado.startswith("M") and caminho_quadrado.endswith("Z")
    assert "Q" in caminho_circulo


def test_vetorizar_descarta_manchas_abaixo_da_area_minima():
    mascara = _mascara(40, 40, lambda x, y: (5 <= x < 25 and 5 <= y < 25) or (x, y) == (35, 35))

    with_ruido = vetorizar(mascara, area_minima=0.5)
    sem_ruido = vetorizar(mascara, area_minima=12.0)

    assert with_ruido.count("M") == 2
    assert sem_ruido.count("M") == 1


def test_vetorizar_de_mascara_vazia_devolve_caminho_vazio():
    assert vetorizar(_mascara(8, 8, lambda x, y: False)) == ""


# --- Derivação dos assets ----------------------------------------------------


def _logo_sintetica() -> Image.Image:
    """Fundo creme, um "símbolo" em 2 tons no topo e um "nome" mais abaixo."""
    imagem = Image.new("RGB", (60, 60), (250, 247, 240))
    for y in range(10, 20):
        for x in range(10, 50):
            imagem.putpixel((x, y), (12, 82, 118) if x < 30 else (35, 112, 148))
    for y in range(40, 50):
        for x in range(10, 50):
            imagem.putpixel((x, y), (12, 82, 118))
    return imagem


def test_detectar_fundo_le_a_moldura_da_imagem():
    assert detectar_fundo(_logo_sintetica()) == (250, 247, 240)


def test_recortar_conteudo_remove_a_moldura_de_fundo():
    recorte = recortar_conteudo(_logo_sintetica(), (250, 247, 240))

    assert recorte.size == (40, 40)


def test_recortar_conteudo_falha_em_imagem_sem_marca():
    with pytest.raises(MarcaError):
        recortar_conteudo(Image.new("RGB", (10, 10), (250, 247, 240)), (250, 247, 240))


def test_extrair_tons_devolve_do_mais_escuro_ao_mais_claro():
    tons = extrair_tons(recortar_conteudo(_logo_sintetica(), (250, 247, 240)), (250, 247, 240))

    assert len(tons) == 2
    assert tons[0] == (12, 82, 118)
    assert tons[1][2] > tons[0][2]


def test_linha_de_corte_separa_simbolo_do_nome():
    recorte = recortar_conteudo(_logo_sintetica(), (250, 247, 240))
    rotulos = [
        [0 if all(abs(c - f) <= 18 for c, f in zip(recorte.getpixel((x, y)), (250, 247, 240), strict=False)) else 1 for x in range(recorte.width)]
        for y in range(recorte.height)
    ]

    # Símbolo nas linhas 0-9 do recorte, nome a partir da linha 30.
    assert linha_de_corte(rotulos) == 10


def test_montar_png_zera_o_fundo_e_preserva_a_marca():
    recorte = recortar_conteudo(_logo_sintetica(), (250, 247, 240))

    png = montar_png(recorte, (250, 247, 240), [(12, 82, 118), (35, 112, 148)]).convert("RGBA")

    assert png.getpixel((0, 20))[3] == 0  # faixa vazia entre símbolo e nome
    assert png.getpixel((5, 2))[3] == 255
    assert png.getpixel((5, 2))[:3] == (12, 82, 118)


def test_montar_svg_produz_xml_valido_com_viewbox():
    svg = montar_svg(40, 30, [("#0c5276", "M0,0L10,0L10,10L0,10Z")])

    raiz = ET.fromstring(svg)

    assert raiz.get("viewBox") == "0 0 40 30"
    assert [caminho.get("fill") for caminho in raiz.iter(f"{SVG_NS}path")] == ["#0c5276"]


# --- Artefatos versionados ---------------------------------------------------


@pytest.mark.parametrize(
    "nome", ["logo-garra.svg", "logo-garra-negativa.svg", "logo-garra-simbolo.svg"]
)
def test_svg_versionado_e_vetor_de_verdade(nome: str):
    raiz = ET.fromstring((ASSETS / nome).read_text(encoding="utf-8"))
    caminhos = list(raiz.iter(f"{SVG_NS}path"))

    assert raiz.get("viewBox"), "sem viewBox o SVG não escala no cabeçalho do relatório"
    assert caminhos and all(len(caminho.get("d", "")) > 100 for caminho in caminhos)
    # Um raster embrulhado em <svg> continuaria sendo raster: não pode haver <image>.
    assert not list(raiz.iter(f"{SVG_NS}image"))


def test_svg_versionado_usa_a_paleta_registrada_em_marca_json():
    metadados = json.loads((ASSETS / "marca.json").read_text(encoding="utf-8"))
    raiz = ET.fromstring((ASSETS / "logo-garra.svg").read_text(encoding="utf-8"))

    fills = [caminho.get("fill") for caminho in raiz.iter(f"{SVG_NS}path")]

    assert fills == [metadados["paleta"]["escuro"], metadados["paleta"]["claro"]]


def test_png_versionado_tem_fundo_transparente():
    png = Image.open(ASSETS / "logo-garra.png").convert("RGBA")
    alfa = png.tobytes()[3::4]

    assert png.getpixel((0, 0))[3] == 0
    # O máximo não é exatamente 255: o alfa também passa pela quantização de paleta.
    assert max(alfa) >= 250


def test_marca_json_registra_a_procedencia_sem_dado_de_cliente():
    metadados = json.loads((ASSETS / "marca.json").read_text(encoding="utf-8"))

    assert len(metadados["origem"]["sha256"]) == 64
    assert "arquivo" not in metadados["origem"]
    assert math.isclose(metadados["tolerancia_px"], 0.6)
