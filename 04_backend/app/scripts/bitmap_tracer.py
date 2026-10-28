"""Vetorizador determinístico de bitmap: máscara booleana → caminhos SVG.

Usado para converter as variantes JPEG da marca oficial (as únicas que o
cliente possui) em vetor com fundo transparente — última pendência de B-02
(RN-07/ADR-13). O resultado é versionado no repositório, então precisa ser
reprodutível byte a byte: nenhuma etapa usa aleatoriedade, dicionário sem
ordem definida ou biblioteca nativa de tracing.

Etapas:

1. `extrair_contornos` — segue as "trincas" (arestas entre pixel de frente e
   de fundo) e as encadeia em laços fechados, com coordenadas inteiras na
   grade de cantos de pixel.
2. `simplificar` — Douglas-Peucker: remove a escada de 1px sem deformar o
   traço além da tolerância pedida.
3. `caminho_svg` — emite o atributo `d`: reta nos cantos vivos (prédios,
   telhados) e Bézier quadrática nos vértices de curva (tipografia).
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence

Ponto = tuple[float, float]
PontoInteiro = tuple[int, int]
Mascara = Sequence[Sequence[bool]]


def extrair_contornos(mascara: Mascara) -> list[list[PontoInteiro]]:
    """Extrai os contornos fechados da região de frente da máscara.

    Cada contorno é uma lista de vértices inteiros na grade de cantos de pixel
    (`0..largura`, `0..altura`). Contornos externos e furos são devolvidos
    juntos, com sentidos opostos — o SVG os renderiza corretamente com
    `fill-rule="evenodd"`.
    """
    altura = len(mascara)
    largura = len(mascara[0]) if altura else 0
    saidas: dict[PontoInteiro, list[PontoInteiro]] = defaultdict(list)

    for y in range(altura):
        linha = mascara[y]
        acima = mascara[y - 1] if y else None
        abaixo = mascara[y + 1] if y + 1 < altura else None
        for x in range(largura):
            if not linha[x]:
                continue
            if acima is None or not acima[x]:
                saidas[(x, y)].append((x + 1, y))
            if x + 1 == largura or not linha[x + 1]:
                saidas[(x + 1, y)].append((x + 1, y + 1))
            if abaixo is None or not abaixo[x]:
                saidas[(x + 1, y + 1)].append((x, y + 1))
            if x == 0 or not linha[x - 1]:
                saidas[(x, y + 1)].append((x, y))

    contornos: list[list[PontoInteiro]] = []
    for inicio in sorted(saidas):
        while saidas[inicio]:
            contorno = _seguir(saidas, inicio)
            if len(contorno) >= 4:
                contornos.append(contorno)
    return contornos


def _seguir(saidas: dict[PontoInteiro, list[PontoInteiro]], inicio: PontoInteiro) -> list[PontoInteiro]:
    pontos = [inicio]
    atual = inicio
    direcao: PontoInteiro | None = None
    while True:
        opcoes = saidas[atual]
        if not opcoes:
            break
        proximo = _escolher(atual, opcoes, direcao)
        opcoes.remove(proximo)
        direcao = (proximo[0] - atual[0], proximo[1] - atual[1])
        atual = proximo
        if atual == inicio:
            break
        pontos.append(atual)
    return pontos


def _escolher(
    atual: PontoInteiro, opcoes: list[PontoInteiro], direcao: PontoInteiro | None
) -> PontoInteiro:
    """Resolve o vértice ambíguo (dois pixels de frente encostados na diagonal).

    Virar primeiro no sentido anti-horário mantém a região de frente
    8-conectada, preservando traços finos em diagonal em vez de parti-los em
    dois contornos soltos.
    """
    if direcao is None or len(opcoes) == 1:
        return min(opcoes)
    dx, dy = direcao
    # Eixo y cresce para baixo: (dy, -dx) é a curva anti-horária na tela.
    for giro in ((dy, -dx), (dx, dy), (-dy, dx), (-dx, -dy)):
        candidata = (atual[0] + giro[0], atual[1] + giro[1])
        if candidata in opcoes:
            return candidata
    return min(opcoes)


def area(contorno: Sequence[Ponto]) -> float:
    """Área com sinal (fórmula do cadarço) — o sinal indica o sentido do laço."""
    total = 0.0
    n = len(contorno)
    for i in range(n):
        x1, y1 = contorno[i]
        x2, y2 = contorno[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return total / 2


def simplificar(contorno: Sequence[PontoInteiro], tolerancia: float) -> list[PontoInteiro]:
    """Douglas-Peucker sobre um laço fechado.

    O laço é rotacionado para começar no vértice lexicograficamente menor
    (sempre um canto real do contorno) e tratado como uma polilinha aberta,
    o que torna o resultado independente de onde o rastreamento começou.
    """
    if len(contorno) < 4 or tolerancia <= 0:
        return list(contorno)
    inicio = min(range(len(contorno)), key=lambda i: contorno[i])
    rotacionado = list(contorno[inicio:]) + list(contorno[:inicio])
    aberto = rotacionado + [rotacionado[0]]
    reduzido = _douglas_peucker(aberto, tolerancia)
    return reduzido[:-1]


def _douglas_peucker(pontos: list[PontoInteiro], tolerancia: float) -> list[PontoInteiro]:
    # Iterativo de propósito: um contorno do original tem dezenas de milhares
    # de vértices e a versão recursiva estoura o limite de recursão do Python.
    total = len(pontos)
    if total < 3:
        return list(pontos)
    manter = [False] * total
    manter[0] = manter[total - 1] = True
    pilha = [(0, total - 1)]
    while pilha:
        inicio, fim = pilha.pop()
        if fim <= inicio + 1:
            continue
        a, b = pontos[inicio], pontos[fim]
        indice, maior = -1, tolerancia
        for i in range(inicio + 1, fim):
            distancia = _distancia_ao_segmento(pontos[i], a, b)
            if distancia > maior:
                indice, maior = i, distancia
        if indice >= 0:
            manter[indice] = True
            pilha.append((inicio, indice))
            pilha.append((indice, fim))
    return [ponto for ponto, guardar in zip(pontos, manter) if guardar]


def _distancia_ao_segmento(ponto: Ponto, inicio: Ponto, fim: Ponto) -> float:
    px, py = ponto
    ax, ay = inicio
    bx, by = fim
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def caminho_svg(contorno: Sequence[Ponto], *, limiar_canto_graus: float = 60.0) -> str:
    """Emite o atributo `d` de um contorno já simplificado.

    Vértices com curva suave (deflexão menor que `limiar_canto_graus`) viram
    Bézier quadrática entre os pontos médios das arestas vizinhas — é o que
    devolve a curvatura da tipografia perdida na escada de pixels. Cantos
    vivos (telhados, janelas, prédios) continuam como reta.
    """
    n = len(contorno)
    if n < 3:
        return ""
    meios = [_meio(contorno[i], contorno[(i + 1) % n]) for i in range(n)]
    suaves = [
        _e_suave(contorno[(i - 1) % n], contorno[i], contorno[(i + 1) % n], limiar_canto_graus) for i in range(n)
    ]

    comandos: list[tuple[str, ...]] = []
    for i in range(n):
        if suaves[i]:
            comandos.append(("Q", _fmt(contorno[i]), _fmt(meios[i])))
        else:
            comandos.append(("L", _fmt(contorno[i])))
            if suaves[(i + 1) % n]:
                comandos.append(("L", _fmt(meios[i])))

    partes = [f"M{comandos[-1][-1]}"]
    for comando in comandos:
        partes.append(comando[0] + " ".join(comando[1:]))
    partes.append("Z")
    return "".join(partes)


def _meio(a: Ponto, b: Ponto) -> Ponto:
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def _e_suave(anterior: Ponto, vertice: Ponto, proximo: Ponto, limiar_graus: float) -> bool:
    ax, ay = vertice[0] - anterior[0], vertice[1] - anterior[1]
    bx, by = proximo[0] - vertice[0], proximo[1] - vertice[1]
    if (ax == 0 and ay == 0) or (bx == 0 and by == 0):
        return False
    cosseno = (ax * bx + ay * by) / (math.hypot(ax, ay) * math.hypot(bx, by))
    deflexao = math.degrees(math.acos(max(-1.0, min(1.0, cosseno))))
    return deflexao < limiar_graus


def _fmt(ponto: Ponto) -> str:
    x = f"{ponto[0]:.1f}".rstrip("0").rstrip(".")
    y = f"{ponto[1]:.1f}".rstrip("0").rstrip(".")
    return f"{x or '0'},{y or '0'}"


def vetorizar(
    mascara: Mascara,
    *,
    tolerancia: float = 0.6,
    area_minima: float = 12.0,
    limiar_canto_graus: float = 60.0,
) -> str:
    """Máscara booleana → atributo `d` único com todos os contornos.

    `area_minima` descarta as manchas de 2-3 pixels que a compressão JPEG do
    original deixa nas bordas; contornos legítimos (até as janelas das casas)
    são ordens de grandeza maiores.
    """
    partes: list[str] = []
    for contorno in extrair_contornos(mascara):
        if abs(area(contorno)) < area_minima:
            continue
        simplificado = simplificar(contorno, tolerancia)
        caminho = caminho_svg(simplificado, limiar_canto_graus=limiar_canto_graus)
        if caminho:
            partes.append(caminho)
    return "".join(partes)
