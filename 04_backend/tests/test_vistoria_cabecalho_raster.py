"""Logo raster no cabeçalho corrido das Vistorias (T92, DEC-54).

O WeasyPrint 70 redesenha o SVG vetorizado da marca (76 KB) em cada página de um
elemento `position: running()`: ~24 s de `write_pdf` em 200 páginas da Vistoria
Residencial (T76). Os geradores passam a embutir o PNG da marca no cabeçalho;
o SVG (`logo_data_uri`) continua só na capa.

Trava, nos dois `.html.j2` versionados (Cautelar e Residencial) e na saída dos
geradores:

- o CSS e o HTML de `.cabecalho` e `.rodape` não citam `image/svg+xml` nem `.svg`,
  nem mesmo depois de renderizados com o `logo_data_uri` SVG que o pipeline injeta;
- o PNG embutido é byte a byte `templates/assets/logo-garra.png`, com resolução
  ≥ 300 dpi na largura do cabeçalho;
- o PNG tem a proporção do SVG (viewBox), com tolerância declarada abaixo, e a
  largura do logo no CSS continua a medida no original (layout inalterado).

Determinístico: só lê arquivos versionados; não precisa de WeasyPrint nem banco.
"""

from __future__ import annotations

import base64
import json
import re
import struct
from pathlib import Path

import jinja2
import pytest

from app.scripts import build_vistoria_cautelar_templates as cautelar
from app.scripts import build_vistoria_residencial_templates as residencial

ASSETS = Path(__file__).resolve().parents[1] / "templates" / "assets"
LOGO_PNG = ASSETS / "logo-garra.png"
LOGO_SVG = ASSETS / "logo-garra.svg"

#: Diferença relativa máxima entre a proporção (largura/altura) do PNG e a do
#: viewBox do SVG. O PNG de `build_brand_assets` é o recorte de 814 x 737 px
#: reduzido a 600 px de largura (arredondamento de 1 px na altura ≈ 0,2 %).
TOLERANCIA_PROPORCAO = 0.005
#: Resolução mínima do raster na largura que o logo ocupa no cabeçalho.
DPI_MINIMO = 300
#: Folga na largura do logo no CSS (pt): a Residencial escreve em cm com 2 casas.
TOLERANCIA_LARGURA_PT = 0.3

SVG_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(b"<svg/>").decode("ascii")

GERADORES = {
    "vistoria_cautelar": cautelar,
    "vistoria_residencial": residencial,
}


def _layout(gerador) -> dict:
    return json.loads(gerador.LAYOUT_JSON.read_text(encoding="utf-8"))


def _fontes(gerador) -> dict[str, str]:
    """O `.html.j2` versionado e o que o gerador produz agora do `layout.json`."""
    return {
        "versionado": gerador.HTML_TEMPLATE.read_text(encoding="utf-8"),
        "gerado": gerador.gerar_html(_layout(gerador)),
    }


def _regras_css(template: str, nome: str) -> list[str]:
    """Regras do `<style>` cujo seletor cita `nome` ou que o puxam (`element(nome)`)."""
    estilo = re.search(r"<style>(.*?)</style>", template, re.S)
    assert estilo, "template sem <style>"
    regras = re.findall(r"([^{}]+)\{([^{}]*)\}", estilo.group(1))
    return [f"{sel.strip()} {{{corpo}}}" for sel, corpo in regras if nome in sel or f"element({nome})" in corpo]


def _elemento(template: str, classe: str) -> str:
    """HTML do `<div class="classe">` do corpo, com os `<div>` aninhados."""
    corpo = template[template.index("<body>"):]
    inicio = corpo.index(f'<div class="{classe}">')
    profundidade = 0
    for marca in re.finditer(r"<div\b|</div>", corpo[inicio:]):
        profundidade += 1 if marca.group() == "<div" else -1
        if profundidade == 0:
            return corpo[inicio:inicio + marca.end()]
    raise AssertionError(f'<div class="{classe}"> sem fechamento')


def _dimensoes_png(conteudo: bytes) -> tuple[int, int]:
    assert conteudo.startswith(b"\x89PNG\r\n\x1a\n"), "não é PNG"
    return struct.unpack(">II", conteudo[16:24])


def _viewbox_svg() -> tuple[float, float]:
    viewbox = re.search(r'viewBox="([\d.\s-]+)"', LOGO_SVG.read_text(encoding="utf-8"))
    assert viewbox, "SVG da marca sem viewBox"
    _, _, largura, altura = (float(valor) for valor in viewbox.group(1).split())
    return largura, altura


def _largura_css_pt(regras: list[str]) -> float:
    regra = next(r for r in regras if r.startswith(".cabecalho img"))
    valor, unidade = re.search(r"width:\s*([\d.]+)(pt|cm)", regra).groups()
    return float(valor) * (72 / 2.54 if unidade == "cm" else 1)


CASOS = [(nome, fonte) for nome in GERADORES for fonte in ("versionado", "gerado")]


@pytest.mark.parametrize(("nome", "fonte"), CASOS)
def test_cabecalho_e_rodape_sem_svg(nome: str, fonte: str) -> None:
    template = _fontes(GERADORES[nome])[fonte]
    for classe in ("cabecalho", "rodape"):
        trechos = [*_regras_css(template, classe), _elemento(template, classe)]
        assert len(trechos) > 1, f"{classe}: CSS não encontrado"
        for trecho in trechos:
            assert "image/svg+xml" not in trecho, f"{nome}/{fonte}: SVG em .{classe}"
            assert ".svg" not in trecho, f"{nome}/{fonte}: .svg em .{classe}"


@pytest.mark.parametrize(("nome", "fonte"), CASOS)
def test_cabecalho_renderizado_ignora_o_svg_do_pipeline(nome: str, fonte: str) -> None:
    """O pipeline injeta `logo_data_uri` em SVG: ele liga o logo, mas o cabeçalho usa o PNG."""
    template = _fontes(GERADORES[nome])[fonte]
    ambiente = jinja2.Environment(autoescape=True)
    cabecalho = _elemento(template, "cabecalho")

    com_logo = ambiente.from_string(cabecalho).render(logo_data_uri=SVG_DATA_URI)
    assert "image/svg+xml" not in com_logo
    assert '<img src="data:image/png;base64,' in com_logo

    sem_logo = ambiente.from_string(cabecalho).render(logo_data_uri=None)
    assert "<img" not in sem_logo


@pytest.mark.parametrize("nome", GERADORES)
def test_capa_continua_com_o_logo_do_contexto(nome: str) -> None:
    """O SVG segue permitido (e usado) na capa: só o cabeçalho corrido mudou."""
    template = _fontes(GERADORES[nome])["versionado"]
    capa = template[template.index('<section class="capa">'):]
    capa = capa[:capa.index("</section>")]
    assert 'src="{{ logo_data_uri }}"' in capa


@pytest.mark.parametrize(("nome", "fonte"), CASOS)
def test_png_embutido_e_o_asset_da_marca(nome: str, fonte: str) -> None:
    gerador = GERADORES[nome]
    template = _fontes(gerador)[fonte]
    src = re.search(r'<img src="data:image/png;base64,([A-Za-z0-9+/=]+)"', _elemento(template, "cabecalho"))
    assert src, "cabeçalho sem PNG embutido"
    embutido = base64.b64decode(src.group(1))
    assert embutido == LOGO_PNG.read_bytes()

    largura_px, _ = _dimensoes_png(embutido)
    largura_pt = _layout(gerador)["cabecalho"]["logo"]["largura_pt"]
    assert largura_px / (largura_pt / 72) >= DPI_MINIMO


@pytest.mark.parametrize("nome", GERADORES)
def test_largura_do_logo_no_cabecalho_inalterada(nome: str) -> None:
    gerador = GERADORES[nome]
    regras = _regras_css(_fontes(gerador)["versionado"], "cabecalho")
    largura_layout = _layout(gerador)["cabecalho"]["logo"]["largura_pt"]
    assert _largura_css_pt(regras) == pytest.approx(largura_layout, abs=TOLERANCIA_LARGURA_PT)


def test_png_tem_a_proporcao_do_svg() -> None:
    largura_px, altura_px = _dimensoes_png(LOGO_PNG.read_bytes())
    largura_svg, altura_svg = _viewbox_svg()
    proporcao_png = largura_px / altura_px
    proporcao_svg = largura_svg / altura_svg
    assert abs(proporcao_png - proporcao_svg) / proporcao_svg <= TOLERANCIA_PROPORCAO
    # Mesmo recorte registrado por build_brand_assets para as duas saídas.
    marca = json.loads((ASSETS / "marca.json").read_text(encoding="utf-8"))
    assert tuple(marca["recorte_px"]) == (largura_svg, altura_svg)
