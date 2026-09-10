"""Extração determinística do layout do LTIP a partir do PDF final do cliente.

Segunda metade de ADR-13/DEC-25 (`00_docs/arquitetura.md`): enquanto o RFO nasce
de planilha (`rfo_layout_extractor`, lida com `openpyxl`), o LTIP e as vistorias
circulam como PDF final de alta fidelidade. Aqui as métricas tipográficas são
**medidas** com `pdfplumber` e gravadas em `templates/ltip/layout.json`, do qual
derivam o `.html.j2` do WeasyPrint e o `.docx` do docxtpl — os dois formatos
exigidos por RF-06 saem da mesma especificação e não divergem.

Privacidade (OWASP A02, mesma regra aplicada em BL-12): o `layout.json` é
versionado, então só carrega **geometria e a marca do emitente**. Nada do
exemplar usado como referência — nome do condomínio, endereço do imóvel,
observações técnicas — entra no artefato.

O original fica em `01_output-context/`, fora do controle de versão
(`.gitignore`); o caminho é sempre recebido por parâmetro e a ausência do
arquivo falha explicitamente.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pdfplumber

PONTO_EM_CM = 2.54 / 72
#: Tolerância ao comparar a página com A4 — PDFs reais variam alguns décimos de ponto.
A4_LARGURA_PT = 595.28
A4_ALTURA_PT = 841.89
TOLERANCIA_A4_PT = 2.0

#: Título numerado de seção: "1.", "4.2.", "5.3.1." — o nível é a profundidade da numeração.
RE_TITULO_NUMERADO = re.compile(r"^\d+(\.\d+)*\.$")
#: Legenda de figura do laudo ("Figura 2 – Imagem do imóvel...").
RE_LEGENDA_FIGURA = re.compile(r"^figura\b", re.IGNORECASE)
#: Rótulo da ficha fotográfica do relatório por sistema (RN-11).
RE_ROTULO_FOTO = re.compile(r"^\s*foto\s*n?º?\s*(\d+)\s*$", re.IGNORECASE)
#: Linhas do rodapé que pertencem à marca do emitente (responsável técnico), e não
#: aos dados do imóvel inspecionado naquele exemplar.
RE_RODAPE_EMITENTE = re.compile(r"CREA|@|Eng\.", re.IGNORECASE)

#: Campos da ficha de ocorrência do relatório fotográfico, na ordem em que
#: aparecem no original. Servem de âncora para reconhecer a ficha e de rótulo
#: nos templates gerados.
CAMPOS_FICHA = (
    "SITUAÇÃO",
    "PRIORIDADE",
    "GRAVIDADE",
    "URGÊNCIA",
    "TENDÊNCIA",
    "PONTUAÇÃO",
    "CLASSIFICAÇÃO",
    "GRAU DE RISCO",
    "SISTEMA",
    "SUBSISTEMA",
    "LOCALIZAÇÃO",
    "OBSERVAÇÕES TÉCNICAS",
)


class LayoutExtractionError(RuntimeError):
    """Erro irrecuperável ao ler o original — nunca degrada para valor inventado."""


def _familia(fontname: str) -> str:
    """Remove o prefixo de subconjunto do PDF (`BAAAAA+OpenSans-Bold` -> `OpenSans-Bold`)."""
    return fontname.split("+")[-1]


def _familia_legivel(fontname: str) -> str:
    """Converte o nome PostScript da fonte em família CSS.

    `TimesNewRomanPSMT` -> `Times New Roman`. Fontes não mapeadas voltam como
    estão: é melhor um nome estranho no CSS do que uma família inventada.
    """
    base = _familia(fontname).split("-")[0]
    base = re.sub(r"(PSMT|MT|PS)$", "", base)
    conhecidas = {
        "TimesNewRoman": "Times New Roman",
        "Arial": "Arial",
        "Calibri": "Calibri",
        "OpenSans": "Open Sans",
        "Helvetica": "Helvetica",
    }
    return conhecidas.get(base, base)


def _e_negrito(fontname: str) -> bool:
    return "bold" in fontname.lower()


def _paginas_de_corpo(pdf: pdfplumber.PDF, *, inicio: int, amostra: int) -> list[Any]:
    """Páginas de texto corrido, usadas para medir margens e corpo.

    Pula a capa e o sumário (`inicio`) e descarta páginas com imagem, cujo texto
    é dominado por legendas de figura e não representa o bloco de texto.
    """
    paginas = [pagina for pagina in pdf.pages[inicio : inicio + amostra] if not pagina.images and pagina.chars]
    if not paginas:
        raise LayoutExtractionError(
            "Nenhuma página de texto corrido encontrada para medir o layout. "
            "Confira se o PDF informado é o laudo completo."
        )
    return paginas


def _extrair_tipografia(paginas: list[Any], paginas_com_figura: list[Any]) -> dict[str, Any]:
    """Corpo, título e legenda a partir da distribuição real de fonte/corpo."""
    corpo = Counter()
    titulos = Counter()
    for pagina in paginas:
        for caractere in pagina.chars:
            chave = (_familia(caractere["fontname"]), round(float(caractere["size"]), 1))
            corpo[chave] += 1
            if _e_negrito(caractere["fontname"]):
                titulos[chave] += 1

    (fonte_corpo, tamanho_corpo), _quantidade = corpo.most_common(1)[0]
    familia = _familia_legivel(fonte_corpo)

    # Título = maior corpo entre as fontes em negrito; se o laudo não usar negrito
    # em títulos, cai para o próprio corpo em vez de chutar um valor.
    tamanho_titulo = max((tamanho for (_, tamanho) in titulos), default=tamanho_corpo)
    return {
        "familia": familia,
        "familia_postscript": fonte_corpo,
        "corpo_pt": tamanho_corpo,
        "titulo_pt": tamanho_titulo,
        "legenda_pt": _corpo_da_legenda(paginas_com_figura, tamanho_corpo),
    }


def _corpo_da_legenda(paginas_com_figura: list[Any], tamanho_corpo: float) -> float:
    """Corpo das legendas de figura, medido nas páginas que de fato têm figura.

    As legendas não aparecem nas páginas de texto corrido usadas para as demais
    métricas — medi-las ali daria o corpo errado.
    """
    tamanhos = Counter()
    for pagina in paginas_com_figura:
        for palavra in pagina.extract_words(extra_attrs=["size"]):
            if RE_LEGENDA_FIGURA.match(palavra["text"]):
                tamanhos[round(float(palavra["size"]), 1)] += 1
    return tamanhos.most_common(1)[0][0] if tamanhos else tamanho_corpo


def _extrair_margens(paginas: list[Any], largura_pt: float, altura_pt: float, rodape_topo_pt: float) -> dict[str, float]:
    """Margens em cm, pela borda mais frequente do bloco de texto.

    Usa a moda (não o mínimo) porque uma única figura ou nota de rodapé
    desalinhada puxaria o extremo e produziria uma margem irreal.
    """
    esquerda, direita, topo = Counter(), Counter(), Counter()
    for pagina in paginas:
        palavras = pagina.extract_words()
        if not palavras:
            continue
        esquerda[round(min(palavra["x0"] for palavra in palavras))] += 1
        direita[round(max(palavra["x1"] for palavra in palavras))] += 1
        topo[round(min(palavra["top"] for palavra in palavras))] += 1

    borda_esquerda = esquerda.most_common(1)[0][0]
    borda_direita = direita.most_common(1)[0][0]
    borda_topo = topo.most_common(1)[0][0]
    return {
        "esquerda": round(borda_esquerda * PONTO_EM_CM, 2),
        "direita": round((largura_pt - borda_direita) * PONTO_EM_CM, 2),
        "superior": round(borda_topo * PONTO_EM_CM, 2),
        "inferior": round((altura_pt - rodape_topo_pt) * PONTO_EM_CM, 2),
    }


def _extrair_rodape(paginas: list[Any], altura_pt: float) -> dict[str, Any]:
    """Linhas fixas do rodapé (marca do responsável técnico) e numeração de página.

    Só sobrevive o que casa `RE_RODAPE_EMITENTE` — o resto do rodapé de um
    exemplar específico não vai para o artefato versionado (A02).
    """
    limite = altura_pt * 0.9
    linhas: dict[float, str] = {}
    topo_minimo = altura_pt
    numeracao = False
    for pagina in paginas:
        agrupadas: dict[int, list[Any]] = {}
        for palavra in pagina.extract_words():
            if palavra["top"] < limite:
                continue
            agrupadas.setdefault(round(palavra["top"]), []).append(palavra)
        for topo, palavras in agrupadas.items():
            texto = " ".join(palavra["text"] for palavra in sorted(palavras, key=lambda item: item["x0"]))
            if texto.strip().isdigit():
                numeracao = True
                continue
            if RE_RODAPE_EMITENTE.search(texto):
                linhas.setdefault(float(topo), texto)
                topo_minimo = min(topo_minimo, float(topo))
    return {
        "linhas": [linhas[topo] for topo in sorted(linhas)],
        "numeracao_pagina": numeracao,
        "topo_pt": round(topo_minimo, 1) if linhas else round(altura_pt, 1),
    }


def _extrair_capa(pagina: Any) -> dict[str, Any]:
    """Título de capa (maior corpo da página) e caixa da logo ancorada no topo."""
    if not pagina.chars:
        raise LayoutExtractionError("A primeira página do PDF não tem texto — capa inesperada.")
    maior = max(float(caractere["size"]) for caractere in pagina.chars)
    titulo = " ".join(
        palavra["text"]
        for palavra in pagina.extract_words(extra_attrs=["size"])
        if abs(float(palavra["size"]) - maior) < 0.5
    )
    fonte_titulo = Counter(
        _familia(caractere["fontname"]) for caractere in pagina.chars if abs(float(caractere["size"]) - maior) < 0.5
    ).most_common(1)[0][0]

    # Sangrada = imagem que cobre praticamente a página inteira; a logo é a menor
    # das imagens restantes ancoradas no topo.
    area_pagina = float(pagina.width) * float(pagina.height)
    de_fundo = [
        imagem for imagem in pagina.images if float(imagem["width"]) * float(imagem["height"]) >= area_pagina * 0.9
    ]
    candidatas = [
        imagem
        for imagem in pagina.images
        if imagem not in de_fundo and float(imagem["top"]) < float(pagina.height) * 0.25
    ]
    logo = min(candidatas, key=lambda imagem: imagem["width"] * imagem["height"], default=None)
    return {
        "titulo": {
            "texto": titulo,
            "fonte_pt": round(maior, 1),
            "familia": _familia_legivel(fonte_titulo),
        },
        "logo": (
            {
                "x_pt": round(float(logo["x0"]), 1),
                "topo_pt": round(float(logo["top"]), 1),
                "largura_pt": round(float(logo["width"]), 1),
                "altura_pt": round(float(logo["height"]), 1),
            }
            if logo is not None
            else None
        ),
        "imagem_de_fundo": bool(de_fundo),
    }


def _extrair_hierarquia_de_titulos(paginas: list[Any]) -> list[dict[str, Any]]:
    """Níveis de título numerados (`1.`, `1.1.`, `4.2.1.`) com o corpo medido em cada um."""
    niveis: dict[int, Counter] = {}
    for pagina in paginas:
        for palavra in pagina.extract_words(extra_attrs=["size", "fontname"]):
            texto = palavra["text"]
            if not RE_TITULO_NUMERADO.match(texto) or not _e_negrito(palavra["fontname"]):
                continue
            nivel = texto.rstrip(".").count(".") + 1
            niveis.setdefault(nivel, Counter())[round(float(palavra["size"]), 1)] += 1
    return [
        {"nivel": nivel, "fonte_pt": tamanhos.most_common(1)[0][0], "negrito": True}
        for nivel, tamanhos in sorted(niveis.items())
    ]


def _extrair_relatorio_fotografico(pdf: pdfplumber.PDF) -> dict[str, Any]:
    """Grade e campos da ficha de ocorrência do relatório fotográfico (RN-11).

    Cada ficha é uma foto + a tabela de classificação da ocorrência. O original
    traz duas fichas por página; a contagem é medida, não assumida.
    """
    fichas_por_pagina = Counter()
    rotulo = None
    campos_vistos: list[str] = []
    for pagina in pdf.pages:
        palavras = [palavra["text"] for palavra in pagina.extract_words()]
        texto_linhas = (pagina.extract_text() or "").splitlines()
        rotulos = [linha for linha in texto_linhas if RE_ROTULO_FOTO.match(linha.strip())]
        if not rotulos:
            continue
        fichas_por_pagina[len(rotulos)] += 1
        if rotulo is None:
            rotulo = re.sub(r"\d+", "", rotulos[0]).strip()
        if not campos_vistos:
            texto_pagina = " ".join(palavras).upper()
            campos_vistos = [campo for campo in CAMPOS_FICHA if campo in texto_pagina]

    if not fichas_por_pagina:
        raise LayoutExtractionError(
            "Nenhuma ficha fotográfica ('Foto nº N') encontrada no PDF — "
            "o relatório fotográfico por sistema (RN-11) é obrigatório no LTIP."
        )
    return {
        "fichas_por_pagina": fichas_por_pagina.most_common(1)[0][0],
        "rotulo_foto": rotulo or "Foto nº",
        "campos": campos_vistos or list(CAMPOS_FICHA),
    }


def _sha256(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def extrair_layout(
    caminho_pdf: Path,
    *,
    tipo_documento: str = "LTIP",
    pagina_inicial_corpo: int = 5,
    amostra_paginas: int = 40,
) -> dict[str, Any]:
    """Lê o PDF final do laudo e devolve a especificação de layout como dicionário.

    `pagina_inicial_corpo` pula capa e sumário; `amostra_paginas` limita a
    varredura (o original tem ~200 páginas e a medição estabiliza bem antes).
    """
    if not caminho_pdf.is_file():
        raise LayoutExtractionError(
            f"Original não encontrado em {caminho_pdf}. "
            "Os arquivos de 01_output-context/ ficam fora do Git — informe o caminho local."
        )

    with pdfplumber.open(caminho_pdf) as pdf:
        if not pdf.pages:
            raise LayoutExtractionError(f"{caminho_pdf.name} não tem páginas.")

        primeira = pdf.pages[0]
        largura_pt = round(float(primeira.width), 2)
        altura_pt = round(float(primeira.height), 2)
        paginas_corpo = _paginas_de_corpo(pdf, inicio=pagina_inicial_corpo, amostra=amostra_paginas)
        amostra = pdf.pages[pagina_inicial_corpo : pagina_inicial_corpo + amostra_paginas]
        paginas_com_figura = [pagina for pagina in amostra if pagina.images]
        rodape = _extrair_rodape(paginas_corpo, altura_pt)

        e_a4 = (
            abs(largura_pt - A4_LARGURA_PT) < TOLERANCIA_A4_PT and abs(altura_pt - A4_ALTURA_PT) < TOLERANCIA_A4_PT
        )
        return {
            "versao_schema": 1,
            "tipo_documento": tipo_documento,
            "origem": {
                # O nome do arquivo original identifica o cliente inspecionado
                # ("... - Cond. <nome>.pdf") e o layout.json é versionado: guarda-se
                # apenas o hash, que basta para rastrear qual exemplar gerou o layout.
                "sha256": _sha256(caminho_pdf),
                "paginas": len(pdf.pages),
            },
            "pagina": {
                "tamanho": "A4" if e_a4 else f"{largura_pt}x{altura_pt}pt",
                "orientacao": "portrait" if altura_pt >= largura_pt else "landscape",
                "largura_pt": largura_pt,
                "altura_pt": altura_pt,
                "margens_cm": _extrair_margens(paginas_corpo, largura_pt, altura_pt, rodape["topo_pt"]),
            },
            "tipografia": _extrair_tipografia(paginas_corpo, paginas_com_figura),
            "titulos": _extrair_hierarquia_de_titulos(amostra),
            "cores": {"texto": "#000000", "cabecalho_secao_fundo": "#D9D9D9"},
            "capa": _extrair_capa(primeira),
            "rodape": rodape,
            "relatorio_fotografico": _extrair_relatorio_fotografico(pdf),
        }
