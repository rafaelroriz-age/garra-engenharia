"""Deriva os assets vetoriais/transparentes da marca a partir do JPEG oficial.

Última pendência de B-02 (RN-07): o cliente só possui a marca em JPEG, com
fundo chapado embutido no arquivo — inutilizável no cabeçalho dos relatórios
(ADR-13) e no ícone da PWA. Este script faz o caminho inverso, de forma
determinística e reprodutível a partir do repositório:

    03_frontend/public/brand/logos/logo-principal-fundo-claro.jpg
        -> app/scripts/bitmap_tracer (contornos -> caminhos SVG)
        -> 04_backend/templates/assets/logo-garra.svg          (PDF/WeasyPrint)
        -> 04_backend/templates/assets/logo-garra.png          (DOCX/python-docx)
        -> 04_backend/templates/assets/marca.json              (procedência)
        -> 03_frontend/public/brand/logo-garra*.svg            (app/PWA)

Uso:

    python -m app.scripts.build_brand_assets
    python -m app.scripts.build_brand_assets --original <outro.jpg>

Os arquivos gerados são versionados; o script só precisa ser reexecutado
quando o cliente enviar uma nova versão da marca.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter

from app.scripts.bitmap_tracer import vetorizar

RAIZ = Path(__file__).resolve().parents[3]
ORIGEM_PADRAO = RAIZ / "03_frontend" / "public" / "brand" / "logos" / "logo-principal-fundo-claro.jpg"
DESTINO_BACKEND = RAIZ / "04_backend" / "templates" / "assets"
DESTINO_FRONTEND = RAIZ / "03_frontend" / "public" / "brand"

NOME_MARCA = "Garra Perícias e Avaliações"
BRANCO = "#ffffff"

# Distância máxima por canal até a cor de fundo para o pixel ainda ser
# considerado fundo. Acima disso o pixel é marca; entre os dois limiares fica
# a borda suavizada do JPEG, usada apenas para calcular o alfa do PNG.
LIMIAR_FUNDO = 18
LIMIAR_FRENTE = 45

CABECALHO_GERADO = (
    "ARQUIVO GERADO — não editar à mão. Produzido por "
    "`python -m app.scripts.build_brand_assets` a partir da marca oficial em JPEG (RN-07/B-02)."
)

Cor = tuple[int, int, int]


class MarcaError(RuntimeError):
    """Falha ao derivar os assets da marca."""


def _distancia(cor: Cor, outra: Cor) -> int:
    return max(abs(cor[0] - outra[0]), abs(cor[1] - outra[1]), abs(cor[2] - outra[2]))


def _distancia_quadrada(cor: Cor, outra: Cor) -> int:
    return (cor[0] - outra[0]) ** 2 + (cor[1] - outra[1]) ** 2 + (cor[2] - outra[2]) ** 2


def _luminancia(cor: Cor) -> float:
    return 0.299 * cor[0] + 0.587 * cor[1] + 0.114 * cor[2]


def _pixels(imagem: Image.Image) -> list[Cor]:
    """Pixels da imagem como tuplas RGB.

    Via `tobytes()` de propósito: `getdata()` está depreciado no Pillow 12 e
    `get_flattened_data()` não existe no Pillow 10 fixado em `requirements.txt`.
    """
    dados = imagem.convert("RGB").tobytes()
    return [(dados[i], dados[i + 1], dados[i + 2]) for i in range(0, len(dados), 3)]


def _hex(cor: Cor) -> str:
    return "#{:02x}{:02x}{:02x}".format(*cor)


def detectar_fundo(imagem: Image.Image) -> Cor:
    """Cor de fundo = a mais frequente na moldura de 1px da imagem."""
    largura, altura = imagem.size
    pixels = imagem.load()
    contagem: Counter[Cor] = Counter()
    for x in range(largura):
        contagem[pixels[x, 0]] += 1
        contagem[pixels[x, altura - 1]] += 1
    for y in range(altura):
        contagem[pixels[0, y]] += 1
        contagem[pixels[largura - 1, y]] += 1
    return contagem.most_common(1)[0][0]


def recortar_conteudo(imagem: Image.Image, fundo: Cor) -> Image.Image:
    """Remove a moldura de fundo, deixando o vetor colado no conteúdo."""
    largura, altura = imagem.size
    pixels = imagem.load()
    minimo_x, minimo_y, maximo_x, maximo_y = largura, altura, -1, -1
    for y in range(altura):
        for x in range(largura):
            if _distancia(pixels[x, y], fundo) > LIMIAR_FRENTE:
                minimo_x = min(minimo_x, x)
                minimo_y = min(minimo_y, y)
                maximo_x = max(maximo_x, x)
                maximo_y = max(maximo_y, y)
    if maximo_x < 0:
        raise MarcaError("Nenhum pixel de marca encontrado — confira a cor de fundo do original.")
    return imagem.crop((minimo_x, minimo_y, maximo_x + 1, maximo_y + 1))


def extrair_tons(imagem: Image.Image, fundo: Cor) -> list[Cor]:
    """Os dois azuis da marca, do mais escuro para o mais claro."""
    frente = [cor for cor in _pixels(imagem) if _distancia(cor, fundo) > LIMIAR_FRENTE]
    if not frente:
        raise MarcaError("Nenhum pixel de marca encontrado no recorte.")
    amostra = Image.new("RGB", (len(frente), 1))
    amostra.putdata(frente)
    reduzida = amostra.quantize(colors=2, method=Image.Quantize.MEDIANCUT).convert("RGB")
    tons = sorted(set(_pixels(reduzida)), key=_luminancia)
    return tons if len(tons) == 2 else [tons[0], tons[0]]


def mapear_rotulos(imagem: Image.Image, fundo: Cor, tons: list[Cor]) -> list[list[int]]:
    """0 = fundo, 1 = tom escuro, 2 = tom claro, com filtro de moda 3x3.

    O filtro elimina os pixels isolados que o artefato de compressão JPEG
    deixa na fronteira entre os dois azuis — sem ele, o tom claro vira uma
    nuvem de manchas de 1px em cima do tom escuro.
    """
    largura, altura = imagem.size
    rotulos = Image.new("L", (largura, altura))
    rotulos.putdata(
        [
            0
            if _distancia(cor, fundo) <= LIMIAR_FRENTE
            else (1 if _distancia_quadrada(cor, tons[0]) <= _distancia_quadrada(cor, tons[1]) else 2)
            for cor in _pixels(imagem)
        ]
    )
    rotulos = rotulos.filter(ImageFilter.ModeFilter(3))
    dados = list(rotulos.tobytes())
    return [dados[y * largura : (y + 1) * largura] for y in range(altura)]


def _mascara(rotulos: list[list[int]], valores: set[int]) -> list[list[bool]]:
    return [[valor in valores for valor in linha] for linha in rotulos]


def linha_de_corte(rotulos: list[list[int]]) -> int:
    """Primeira linha da maior faixa horizontal vazia — separa símbolo e nome."""
    vazias = [indice for indice, linha in enumerate(rotulos) if not any(linha)]
    if not vazias:
        raise MarcaError("Não há faixa vazia separando o símbolo do nome da marca.")
    melhor_inicio = inicio = vazias[0]
    melhor_tamanho = tamanho = 1
    for anterior, atual in zip(vazias, vazias[1:]):
        if atual == anterior + 1:
            tamanho += 1
        else:
            inicio, tamanho = atual, 1
        if tamanho > melhor_tamanho:
            melhor_inicio, melhor_tamanho = inicio, tamanho
    return melhor_inicio


def montar_svg(largura: int, altura: int, camadas: list[tuple[str, str]]) -> str:
    caminhos = "\n".join(
        f'  <path fill="{cor}" fill-rule="evenodd" d="{dados}" />' for cor, dados in camadas if dados
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" '
        f'role="img" aria-label="{NOME_MARCA}">\n'
        f"  <!-- {CABECALHO_GERADO} -->\n"
        f"  <title>{NOME_MARCA}</title>\n"
        f"{caminhos}\n"
        f"</svg>\n"
    )


def montar_png(imagem: Image.Image, fundo: Cor, tons: list[Cor], max_lado: int = 600) -> Image.Image:
    """Versão raster com fundo transparente, para o DOCX (que não aceita SVG).

    O alfa vem da distância até a cor de fundo e a cor é "desmisturada"
    (`C = a·F + (1-a)·B` resolvido para `F`), senão a borda suavizada do JPEG
    ficaria com um halo creme sobre qualquer fundo que não o original.
    """
    saida: list[tuple[int, int, int, int]] = []
    for cor in _pixels(imagem):
        distancia = _distancia(cor, fundo)
        if distancia <= LIMIAR_FUNDO:
            saida.append((0, 0, 0, 0))
            continue
        referencia = min(tons, key=lambda tom: _distancia_quadrada(cor, tom))
        escala = _distancia(referencia, fundo) or 1
        alfa = min(1.0, distancia / escala)
        canais = tuple(
            max(0, min(255, round((cor[indice] - (1 - alfa) * fundo[indice]) / alfa))) for indice in range(3)
        )
        saida.append((*canais, round(alfa * 255)))
    png = Image.new("RGBA", imagem.size)
    png.putdata(saida)
    if max(png.size) > max_lado:
        proporcao = max_lado / max(png.size)
        png = png.resize(
            (max(1, round(png.width * proporcao)), max(1, round(png.height * proporcao))), Image.LANCZOS
        )
    # Paleta: a marca tem 2 tons chapados, então 128 cores cobrem com folga o
    # degradê da borda e cortam o arquivo embutido em cada DOCX para ~1/6.
    return png.quantize(colors=128, method=Image.Quantize.FASTOCTREE)


def _gravar(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
    print(f"  {caminho.relative_to(RAIZ)} ({caminho.stat().st_size / 1024:.1f} KB)")


def gerar(origem: Path, tolerancia: float) -> dict[str, Any]:
    if not origem.is_file():
        raise MarcaError(f"Original da marca não encontrado: {origem}")

    imagem = Image.open(origem).convert("RGB")
    fundo = detectar_fundo(imagem)
    recorte = recortar_conteudo(imagem, fundo)
    tons = extrair_tons(recorte, fundo)
    rotulos = mapear_rotulos(recorte, fundo, tons)
    largura, altura = recorte.size
    corte = linha_de_corte(rotulos)

    silhueta = vetorizar(_mascara(rotulos, {1, 2}), tolerancia=tolerancia)
    tom_claro = vetorizar(_mascara(rotulos, {2}), tolerancia=tolerancia)
    simbolo = vetorizar(_mascara(rotulos[:corte], {1, 2}), tolerancia=tolerancia)

    completo = montar_svg(largura, altura, [(_hex(tons[0]), silhueta), (_hex(tons[1]), tom_claro)])
    negativo = montar_svg(largura, altura, [(BRANCO, silhueta)])
    simbolo_svg = montar_svg(largura, corte, [(_hex(tons[0]), simbolo)])

    print("Assets gerados:")
    for destino in (DESTINO_BACKEND, DESTINO_FRONTEND):
        _gravar(destino / "logo-garra.svg", completo)
        _gravar(destino / "logo-garra-negativa.svg", negativo)
        _gravar(destino / "logo-garra-simbolo.svg", simbolo_svg)

    png = montar_png(recorte, fundo, tons)
    DESTINO_BACKEND.mkdir(parents=True, exist_ok=True)
    png.save(DESTINO_BACKEND / "logo-garra.png", optimize=True)
    print(f"  {(DESTINO_BACKEND / 'logo-garra.png').relative_to(RAIZ)} "
          f"({(DESTINO_BACKEND / 'logo-garra.png').stat().st_size / 1024:.1f} KB)")

    return {
        "gerado_em": datetime.now(UTC).isoformat(timespec="seconds"),
        "gerado_por": "app.scripts.build_brand_assets",
        "origem": {
            # Sem o nome/caminho do arquivo: o hash basta para provar a procedência.
            "sha256": hashlib.sha256(origem.read_bytes()).hexdigest(),
            "dimensoes_px": list(imagem.size),
        },
        "recorte_px": [largura, altura],
        "linha_de_corte_simbolo_px": corte,
        "cor_fundo_removida": _hex(fundo),
        "paleta": {"escuro": _hex(tons[0]), "claro": _hex(tons[1])},
        "tolerancia_px": tolerancia,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera os assets vetoriais da marca (B-02/RN-07).")
    parser.add_argument("--original", type=Path, default=ORIGEM_PADRAO, help="JPEG oficial da marca.")
    parser.add_argument(
        "--tolerancia",
        type=float,
        default=0.6,
        help="Desvio máximo, em pixels do original, aceito ao simplificar os contornos.",
    )
    argumentos = parser.parse_args(argv)

    try:
        metadados = gerar(argumentos.original, argumentos.tolerancia)
    except MarcaError as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    destino = DESTINO_BACKEND / "marca.json"
    destino.write_text(json.dumps(metadados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
