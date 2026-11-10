"""Extração determinística do layout do Laudo de Vistoria Cautelar de Recebimento.

Fatia "Vistoria Cautelar" do modelo incremental de ADR-13/DEC-25
(`00_docs/arquitetura.md`), pelo mesmo método do LTIP (`ltip_layout_extractor`,
BL-17): as métricas são **medidas** com `pdfplumber` no PDF final do cliente e
gravadas em `templates/vistoria_cautelar/layout.json`, do qual derivam o
`.html.j2` (WeasyPrint, ADR-01) e o `.docx` (docxtpl, ADR-04).

O que é medido: tamanho de página, margens do bloco de texto, entrelinha,
famílias e corpos tipográficos, cores, cabeçalho (logo), rodapé, sumário,
hierarquia e ordem dos títulos numerados, grade do relatório fotográfico,
tabela do plano de correções e bloco de assinatura.

Privacidade (OWASP A02): o `layout.json` é versionado, então guarda **apenas
geometria e rótulos fixos**. Tudo o que identifica pessoas ou o caso do
exemplar — nome do responsável técnico, CREA, IBAPE, e-mail, telefone, nome do
condomínio, descrição da obra, cidade e data — é descartado e substituído por
placeholders Jinja2 nomeados (`{{ responsavel.nome }}`, `{{ obra.descricao }}`
...). Antes de devolver, `_garantir_sem_dados_pessoais` varre o resultado e
falha se sobrar e-mail, telefone, CPF, CEP ou número de registro (fail-closed).

O original fica em `01_output-context/`, fora do Git; o caminho é sempre
recebido por parâmetro e a ausência do arquivo falha explicitamente.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from itertools import pairwise
from pathlib import Path
from typing import Any

import pdfplumber

from app.scripts.ltip_layout_extractor import (
    A4_ALTURA_PT,
    A4_LARGURA_PT,
    PONTO_EM_CM,
    RE_LEGENDA_FIGURA,
    RE_TITULO_NUMERADO,
    TOLERANCIA_A4_PT,
    LayoutExtractionError,
    _e_negrito,
    _familia,
    _familia_legivel,
    _sha256,
)

__all__ = ["TIPO_DOCUMENTO", "LayoutExtractionError", "extrair_layout", "slug"]

TIPO_DOCUMENTO = "VISTORIA_CAUTELAR"

#: Faixa inferior da página tratada como rodapé (mesmo critério do LTIP).
FRACAO_RODAPE = 0.9
#: Imagem com área >= 90% da página é fundo sangrado (capa).
FRACAO_FUNDO = 0.9
#: Imagem com área >= 10% da página é foto do relatório; menor que isso é logo/assinatura.
FRACAO_FOTO = 0.10
#: Cabeçalho de tabela ocupa ao menos 30% da largura da página (descarta realces de texto).
FRACAO_LARGURA_TABELA = 0.30

# --- Detectores de dado pessoal / do caso (OWASP A02) ---------------------------------
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
RE_TELEFONE = re.compile(r"\(?\b\d{2}\)?\s*9?\s*\d{4}-?\d{4}\b")
RE_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
RE_CEP = re.compile(r"\b\d{5}-\d{3}\b")
#: Sequência longa de dígitos: nº de CREA/IBAPE, CPF/CNPJ sem máscara, telefone colado.
RE_NUMERO_LONGO = re.compile(r"\d{6,}")
RE_CREA = re.compile(r"\bCREA\b", re.IGNORECASE)
RE_COR_HEX = re.compile(r"#[0-9A-F]{6}")

MESES = "janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro"
RE_DATA_EXTENSO = re.compile(rf"\b({MESES})\s+de\s+\d{{4}}\b", re.IGNORECASE)

# --- Estrutura do laudo ----------------------------------------------------------------
RE_PONTILHADO = re.compile(r"\.{5,}")
RE_SUMARIO = re.compile(r"^\s*sum[áa]rio\s*$", re.IGNORECASE)
RE_LINHA_ASSINATURA = re.compile(r"^_{10,}$")
RE_SEPARADOR_LEGENDA = re.compile(r"^figura\s+\d+\s*([-–—])", re.IGNORECASE)  # noqa: RUF001 - travessão real do texto do laudo
RE_FONTE_LEGENDA = re.compile(r"(Fonte:\s*[^.]{1,40}\.)\s*$")
RE_SECAO_FOTOGRAFICA = re.compile(r"fotogr[áa]fico", re.IGNORECASE)
#: "10.1. Parecer Técnico — Recebimento Parcial com Ressalvas": o que vem depois do
#: travessão é o resultado do caso, não rótulo fixo.
RE_COMPLEMENTO_TITULO = re.compile(r"\s+([—–])\s+")  # noqa: RUF001 - travessão real do título do laudo

# --- Placeholders Jinja2 que substituem dado pessoal/do caso ----------------------------
PH_NOME = "{{ responsavel.nome }}"
PH_REGISTRO = "{{ responsavel.titulo_profissional }} - CREA nº {{ responsavel.crea }}"
PH_CONTATO = "{{ responsavel.email }} / {{ responsavel.telefone }}"
PH_DATA_MES_ANO = "{{ data_emissao_mes_ano }}"
PH_LOCAL_DATA = "{{ local_emissao }}, {{ data_emissao_extenso }}."
PH_OBRA = "{{ obra.descricao }}"
PH_EDIFICACAO = "{{ edificacao.nome }}"


def slug(texto: str) -> str:
    """Chave estável em snake_case ASCII (`Plano de Correções` -> `plano_de_correcoes`)."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")


def _cor_hex(cor: Any) -> str | None:
    """Cor do pdfplumber (cinza, RGB ou CMYK em 0..1) em `#RRGGBB`."""
    if cor is None:
        return None
    try:
        if isinstance(cor, (int, float)):
            valores: tuple[float, ...] = (float(cor),) * 3
        else:
            valores = tuple(float(valor) for valor in cor)
            if len(valores) == 1:
                valores = valores * 3
            elif len(valores) == 4:
                c, m, y, k = valores
                valores = ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
            elif len(valores) != 3:
                return None
    except (TypeError, ValueError):
        return None
    return "#" + "".join(f"{round(max(0.0, min(1.0, valor)) * 255):02X}" for valor in valores)


def _e_italico(fontname: str) -> bool:
    nome = fontname.lower()
    return "italic" in nome or "oblique" in nome


def _moda(valores: list[Any], padrao: Any = None) -> Any:
    return Counter(valores).most_common(1)[0][0] if valores else padrao


def _cm(pontos: float) -> float:
    return round(pontos * PONTO_EM_CM, 2) + 0.0  # + 0.0 normaliza -0.0


def _linhas(pagina: Any) -> list[dict[str, Any]]:
    """Palavras agrupadas por linha (topo arredondado), com a fonte da 1ª palavra."""
    agrupadas: dict[int, list[dict[str, Any]]] = {}
    for palavra in pagina.extract_words(extra_attrs=["size", "fontname", "non_stroking_color"]):
        agrupadas.setdefault(round(float(palavra["top"])), []).append(palavra)
    linhas = []
    for topo in sorted(agrupadas):
        palavras = sorted(agrupadas[topo], key=lambda item: item["x0"])
        primeira = palavras[0]
        linhas.append(
            {
                "topo": float(topo),
                "base": max(float(palavra["bottom"]) for palavra in palavras),
                "x0": min(float(palavra["x0"]) for palavra in palavras),
                "x1": max(float(palavra["x1"]) for palavra in palavras),
                "texto": " ".join(palavra["text"] for palavra in palavras),
                "palavras": palavras,
                "tamanho": round(float(primeira["size"]), 1),
                "fonte": _familia(primeira["fontname"]),
                "negrito": _e_negrito(primeira["fontname"]),
                "italico": _e_italico(primeira["fontname"]),
                "cor": _cor_hex(primeira["non_stroking_color"]),
            }
        )
    return linhas


def _alinhamento(x0: float, x1: float, largura_pt: float, margem_direita_pt: float | None = None) -> str:
    centro = (x0 + x1) / 2
    if abs(centro - largura_pt / 2) < 15:
        return "center"
    if x0 > largura_pt / 2 or (margem_direita_pt is not None and abs(x1 - margem_direita_pt) < 4 and x0 > largura_pt * 0.3):
        return "right"
    return "left"


def _blocos(linhas: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Agrupa linhas consecutivas de mesmo corpo e entrelinha curta num bloco."""
    blocos: list[list[dict[str, Any]]] = []
    for linha in linhas:
        if blocos:
            anterior = blocos[-1][-1]
            if anterior["tamanho"] == linha["tamanho"] and linha["topo"] - anterior["topo"] < linha["tamanho"] * 1.8:
                blocos[-1].append(linha)
                continue
        blocos.append([linha])
    return blocos


def _caixa(imagem: dict[str, Any]) -> dict[str, float]:
    return {
        "x_pt": round(float(imagem["x0"]), 1),
        "topo_pt": round(float(imagem["top"]), 1),
        "largura_pt": round(float(imagem["width"]), 1),
        "altura_pt": round(float(imagem["height"]), 1),
    }


def _area(imagem: dict[str, Any]) -> float:
    return float(imagem["width"]) * float(imagem["height"])


# --------------------------------------------------------------------------------------
# Classificação das páginas
# --------------------------------------------------------------------------------------


def _e_pagina_de_sumario(linhas: list[dict[str, Any]]) -> bool:
    return any(RE_SUMARIO.match(linha["texto"]) for linha in linhas) or (
        sum(1 for linha in linhas if RE_PONTILHADO.search(linha["texto"])) >= 3
    )


def _imagens_de_cabecalho(pagina: Any) -> list[dict[str, Any]]:
    """Logo do cabeçalho: imagem pequena inteiramente na faixa superior da página."""
    area_pagina = float(pagina.width) * float(pagina.height)
    return [
        imagem
        for imagem in pagina.images
        if float(imagem["bottom"]) < float(pagina.height) * 0.12 and _area(imagem) < area_pagina * 0.05
    ]


def _fotos(pagina: Any) -> list[dict[str, Any]]:
    area_pagina = float(pagina.width) * float(pagina.height)
    return [
        imagem
        for imagem in pagina.images
        if area_pagina * FRACAO_FOTO <= _area(imagem) < area_pagina * FRACAO_FUNDO
    ]


# --------------------------------------------------------------------------------------
# Medições
# --------------------------------------------------------------------------------------


def _extrair_tipografia(paginas_texto: list[Any], altura_pt: float) -> dict[str, Any]:
    limite = altura_pt * FRACAO_RODAPE
    corpo: Counter = Counter()
    titulos: Counter = Counter()
    for pagina in paginas_texto:
        for caractere in pagina.chars:
            if float(caractere["top"]) >= limite or not caractere["text"].strip():
                continue
            chave = (_familia(caractere["fontname"]), round(float(caractere["size"]), 1))
            corpo[chave] += 1
            if _e_negrito(caractere["fontname"]):
                titulos[chave] += 1
    if not corpo:
        raise LayoutExtractionError("Nenhum texto corrido encontrado para medir a tipografia do laudo.")
    (fonte_corpo, tamanho_corpo), _ = corpo.most_common(1)[0]
    candidatos_titulo = [(tamanho, fonte) for (fonte, tamanho) in titulos if tamanho > tamanho_corpo]
    tamanho_titulo, fonte_titulo = max(candidatos_titulo, default=(tamanho_corpo, fonte_corpo))
    return {
        "familia": _familia_legivel(fonte_corpo),
        "familia_postscript": fonte_corpo,
        "corpo_pt": tamanho_corpo,
        "titulo_pt": tamanho_titulo,
        "familia_titulo": _familia_legivel(fonte_titulo),
    }


def _linhas_de_corpo(
    linhas: list[dict[str, Any]], tipografia: dict[str, Any], limite_rodape: float
) -> list[dict[str, Any]]:
    return [
        linha
        for linha in linhas
        if linha["topo"] < limite_rodape
        and linha["tamanho"] == tipografia["corpo_pt"]
        and linha["fonte"] == tipografia["familia_postscript"]
    ]


def _extrair_pagina_e_paragrafo(
    linhas_texto: list[list[dict[str, Any]]],
    tipografia: dict[str, Any],
    largura_pt: float,
    altura_pt: float,
    topo_rodape_pt: float,
    base_cabecalho_pt: float,
) -> tuple[dict[str, float], dict[str, Any]]:
    """Margens do bloco de texto corrido (moda, não extremo) e métricas de parágrafo."""
    limite = altura_pt * FRACAO_RODAPE
    esquerda: list[int] = []
    direita: list[int] = []
    topo: list[int] = []
    entrelinhas: list[int] = []
    for linhas in linhas_texto:
        do_corpo = _linhas_de_corpo(linhas, tipografia, limite)
        esquerda += [round(linha["x0"]) for linha in do_corpo]
        direita += [round(linha["x1"]) for linha in do_corpo]
        uteis = [linha for linha in linhas if base_cabecalho_pt <= linha["topo"] < limite]
        if uteis:
            topo.append(round(min(linha["topo"] for linha in uteis)))
        for anterior, atual in pairwise(do_corpo):
            passo = round(atual["topo"] - anterior["topo"])
            if 0 < passo < tipografia["corpo_pt"] * 3:
                entrelinhas.append(passo)
    if not esquerda:
        raise LayoutExtractionError("Não foi possível medir o bloco de texto corrido do laudo.")

    borda_esquerda = _moda(esquerda)
    borda_direita = _moda(direita)
    entrelinha = _moda([passo for passo in entrelinhas if passo < tipografia["corpo_pt"] * 1.6], tipografia["corpo_pt"])
    entre_paragrafos = _moda([passo for passo in entrelinhas if passo > entrelinha + 2], entrelinha)
    justificadas = sum(1 for valor in direita if abs(valor - borda_direita) <= 2)
    margens = {
        "esquerda": _cm(borda_esquerda),
        "direita": _cm(largura_pt - borda_direita),
        "superior": _cm(_moda(topo, borda_esquerda)),
        "inferior": _cm(altura_pt - topo_rodape_pt),
    }
    paragrafo = {
        "entrelinha_pt": float(entrelinha),
        "altura_linha": round(entrelinha / tipografia["corpo_pt"], 2),
        "espaco_entre_paragrafos_pt": float(max(entre_paragrafos - entrelinha, 0)),
        "alinhamento": "justify" if justificadas / len(direita) > 0.5 else "left",
    }
    return margens, paragrafo


def _extrair_cabecalho(paginas_corpo: list[Any], largura_pt: float) -> dict[str, Any]:
    caixas = []
    for pagina in paginas_corpo:
        logos = _imagens_de_cabecalho(pagina)
        if logos:
            caixas.append(tuple(_caixa(max(logos, key=_area)).values()))
    if not caixas:
        return {"logo": None, "base_pt": 0.0}
    x_pt, topo_pt, largura, altura = _moda(caixas)
    return {
        "logo": {
            "x_pt": x_pt,
            "topo_pt": topo_pt,
            "largura_pt": largura,
            "altura_pt": altura,
            "alinhamento": _alinhamento(x_pt, x_pt + largura, largura_pt),
        },
        "base_pt": round(topo_pt + altura, 1),
        "paginas_com_logo": len(caixas),
    }


def _modelo_de_linha_do_responsavel(texto: str) -> str:
    """Placeholder de uma linha de identificação do responsável técnico."""
    # CREA antes de telefone: o nº de registro (10 dígitos) também casa RE_TELEFONE.
    if RE_CREA.search(texto):
        return PH_REGISTRO
    if RE_EMAIL.search(texto) or RE_TELEFONE.search(texto):
        return PH_CONTATO
    return PH_NOME


def _extrair_rodape(
    linhas_paginas: list[tuple[int, list[dict[str, Any]]]], largura_pt: float, altura_pt: float
) -> dict[str, Any]:
    """Geometria do rodapé. O texto é descartado: cada linha vira placeholder (A02)."""
    limite = altura_pt * FRACAO_RODAPE
    por_topo: dict[float, list[dict[str, Any]]] = {}
    numeros: list[dict[str, Any]] = []
    for indice, linhas in linhas_paginas:
        for linha in linhas:
            if linha["topo"] < limite:
                continue
            if linha["texto"].strip().isdigit():
                numeros.append({**linha, "indice": indice})
            else:
                por_topo.setdefault(linha["topo"], []).append(linha)

    # Só as posições que se repetem em boa parte das páginas são o rodapé fixo.
    minimo = max(1, len(linhas_paginas) // 2)
    linhas_fixas = []
    for topo in sorted(por_topo):
        ocorrencias = por_topo[topo]
        if len(ocorrencias) < minimo:
            continue
        amostra = ocorrencias[0]
        linhas_fixas.append(
            {
                "modelo": _modelo_de_linha_do_responsavel(_moda([linha["texto"] for linha in ocorrencias])),
                "topo_pt": topo,
                "fonte_pt": _moda([linha["tamanho"] for linha in ocorrencias]),
                "familia": _familia_legivel(amostra["fonte"]),
                "cor": _moda([linha["cor"] for linha in ocorrencias]),
                "alinhamento": _alinhamento(amostra["x0"], amostra["x1"], largura_pt),
            }
        )

    numeracao = None
    if numeros:
        deslocamentos = []
        for numero in numeros:
            deslocamentos.append(int(numero["texto"].strip()) - (numero["indice"] + 1))
        numeracao = {
            "familia": _familia_legivel(_moda([numero["fonte"] for numero in numeros])),
            "fonte_pt": _moda([numero["tamanho"] for numero in numeros]),
            "topo_pt": _moda([numero["topo"] for numero in numeros]),
            "borda_direita_pt": _moda([round(numero["x1"]) for numero in numeros]),
            "alinhamento": "right",
            # Diferença entre o número impresso e a posição física da página no PDF
            # (-1 = a capa não é contada). Aplicada às páginas do corpo.
            "deslocamento": _moda(deslocamentos),
        }

    topo = min((linha["topo_pt"] for linha in linhas_fixas), default=round(altura_pt, 1))
    return {"linhas": linhas_fixas, "numeracao_pagina": numeracao, "topo_pt": topo}


def _extrair_capa(pagina: Any, linhas: list[dict[str, Any]], largura_pt: float) -> dict[str, Any]:
    """Capa: título fixo (1º bloco de maior corpo) e o resto como placeholders."""
    if not linhas:
        raise LayoutExtractionError("A primeira página do PDF não tem texto — capa inesperada.")
    area_pagina = float(pagina.width) * float(pagina.height)
    fundo = [imagem for imagem in pagina.images if _area(imagem) >= area_pagina * FRACAO_FUNDO]
    outras = [imagem for imagem in pagina.images if imagem not in fundo]
    logo = min(
        (imagem for imagem in outras if float(imagem["top"]) < float(pagina.height) * 0.25),
        key=_area,
        default=None,
    )

    blocos = _blocos(linhas)
    maior = max(linha["tamanho"] for linha in linhas)
    indice_titulo = next(indice for indice, bloco in enumerate(blocos) if bloco[0]["tamanho"] == maior)
    titulo = blocos[indice_titulo]

    elementos = []
    subtitulo_usado = False
    for bloco in blocos[indice_titulo + 1 :]:
        textos = [linha["texto"] for linha in bloco]
        primeiro = bloco[0]
        base = {
            "fonte_pt": primeiro["tamanho"],
            "familia": _familia_legivel(primeiro["fonte"]),
            "negrito": primeiro["negrito"],
            "cor": primeiro["cor"],
            "x_pt": round(min(linha["x0"] for linha in bloco), 1),
            "borda_direita_pt": round(max(linha["x1"] for linha in bloco), 1),
            "topo_pt": primeiro["topo"],
            "alinhamento": _alinhamento(
                min(linha["x0"] for linha in bloco), max(linha["x1"] for linha in bloco), largura_pt
            ),
        }
        if any(RE_DATA_EXTENSO.search(texto) for texto in textos):
            elementos.append({**base, "papel": "data", "linhas": ["{{ data_emissao_mes_ano|upper }}"]})
        elif any(texto.rstrip().endswith(":") for texto in textos):
            modelos = []
            for texto in textos:
                if texto.rstrip().endswith(":") and not RE_NUMERO_LONGO.search(texto):
                    modelos.append(texto.strip())
                elif RE_CREA.search(texto):
                    modelos.append("CREA: {{ responsavel.crea }}")
                elif RE_EMAIL.search(texto) or RE_TELEFONE.search(texto):
                    modelos.append(PH_CONTATO)
                else:
                    modelos.append("{{ (responsavel.titulo_profissional ~ ' ' ~ responsavel.nome)|upper }}")
            faixa = next(
                (
                    imagem
                    for imagem in outras
                    if float(imagem["top"]) <= primeiro["topo"] <= float(imagem["bottom"])
                ),
                None,
            )
            elementos.append({**base, "papel": "responsavel", "linhas": modelos, "faixa": _caixa(faixa) if faixa else None})
        elif not subtitulo_usado:
            subtitulo_usado = True
            modelos = [PH_OBRA] + [PH_EDIFICACAO] * (len(textos) - 1) if len(textos) > 1 else [PH_EDIFICACAO]
            elementos.append({**base, "papel": "subtitulo", "linhas": modelos[:2]})
        # Blocos adicionais sem papel reconhecível são conteúdo do caso: descartados.

    return {
        "titulo": {
            "linhas": [linha["texto"] for linha in titulo],
            "fonte_pt": maior,
            "familia": _familia_legivel(titulo[0]["fonte"]),
            "negrito": titulo[0]["negrito"],
            "cor": titulo[0]["cor"],
            "x_pt": round(min(linha["x0"] for linha in titulo), 1),
            "topo_pt": titulo[0]["topo"],
            "entrelinha_pt": round(titulo[1]["topo"] - titulo[0]["topo"], 1) if len(titulo) > 1 else maior,
        },
        "elementos": elementos,
        "logo": _caixa(logo) if logo is not None else None,
        "imagem_de_fundo": bool(fundo),
    }


def _extrair_folha_de_rosto(linhas: list[dict[str, Any]], largura_pt: float, altura_pt: float) -> dict[str, Any] | None:
    """Folha de rosto: título fixo, objeto do laudo e data (os dois últimos viram placeholder)."""
    uteis = [linha for linha in linhas if linha["topo"] < altura_pt * FRACAO_RODAPE]
    if not uteis:
        return None
    blocos = _blocos(uteis)
    maior = max(linha["tamanho"] for linha in uteis)
    indice_titulo = next(indice for indice, bloco in enumerate(blocos) if bloco[0]["tamanho"] == maior)
    titulo = blocos[indice_titulo]
    resultado: dict[str, Any] = {
        "titulo": {
            "linhas": [linha["texto"] for linha in titulo],
            "fonte_pt": maior,
            "familia": _familia_legivel(titulo[0]["fonte"]),
            "negrito": titulo[0]["negrito"],
            "topo_pt": titulo[0]["topo"],
            "alinhamento": _alinhamento(titulo[0]["x0"], titulo[0]["x1"], largura_pt),
        },
        "objeto": None,
        "data": None,
    }
    for bloco in blocos[indice_titulo + 1 :]:
        primeiro = bloco[0]
        geometria = {
            "fonte_pt": primeiro["tamanho"],
            "negrito": primeiro["negrito"],
            "topo_pt": primeiro["topo"],
            "alinhamento": _alinhamento(primeiro["x0"], primeiro["x1"], largura_pt),
        }
        if any(RE_DATA_EXTENSO.search(linha["texto"]) for linha in bloco):
            resultado["data"] = {**geometria, "modelo": PH_DATA_MES_ANO}
        elif resultado["objeto"] is None:
            resultado["objeto"] = {**geometria, "modelo": PH_OBRA, "linhas_medidas": len(bloco)}
    return resultado


def _extrair_sumario(paginas_linhas: list[list[dict[str, Any]]], margem_esquerda_pt: float) -> dict[str, Any] | None:
    if not paginas_linhas:
        return None
    titulo = None
    entradas: list[dict[str, Any]] = []
    pontilhado: list[str] = []
    for linhas in paginas_linhas:
        for linha in linhas:
            if titulo is None and RE_SUMARIO.match(linha["texto"]):
                titulo = linha
                continue
            primeira = linha["palavras"][0]["text"]
            if RE_TITULO_NUMERADO.match(primeira):
                entradas.append({**linha, "nivel": primeira.rstrip(".").count(".") + 1})
            pontilhado += [
                _familia_legivel(palavra["fontname"]) for palavra in linha["palavras"] if RE_PONTILHADO.fullmatch(palavra["text"])
            ]
    recuos = {}
    for nivel in sorted({entrada["nivel"] for entrada in entradas}):
        recuos[str(nivel)] = _cm(_moda([round(e["x0"]) for e in entradas if e["nivel"] == nivel]) - margem_esquerda_pt)
    return {
        "titulo": "SUMÁRIO",
        "titulo_pt": titulo["tamanho"] if titulo else None,
        "titulo_negrito": titulo["negrito"] if titulo else True,
        "entrada_pt": _moda([entrada["tamanho"] for entrada in entradas]),
        "entrada_negrito": _moda([entrada["negrito"] for entrada in entradas], True),
        "familia_entrada": _familia_legivel(_moda([entrada["fonte"] for entrada in entradas], "")),
        "familia_pontilhado": _moda(pontilhado),
        "recuo_por_nivel_cm": recuos,
        "niveis": max((entrada["nivel"] for entrada in entradas), default=0),
    }


def _extrair_titulos(
    linhas_paginas: list[tuple[int, list[dict[str, Any]]]], tipografia: dict[str, Any], altura_pt: float
) -> list[dict[str, Any]]:
    """Títulos numerados do corpo, em ordem, com posição (página, topo) para ancorar blocos."""
    limite = altura_pt * FRACAO_RODAPE
    titulos: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for indice, linhas in linhas_paginas:
        for posicao, linha in enumerate(linhas):
            primeira = linha["palavras"][0]
            if (
                linha["topo"] >= limite
                or not RE_TITULO_NUMERADO.match(primeira["text"])
                or not _e_negrito(primeira["fontname"])
                or linha["tamanho"] <= tipografia["corpo_pt"]
                or RE_PONTILHADO.search(linha["texto"])
            ):
                continue
            numero = primeira["text"].rstrip(".")
            if numero in vistos:
                continue
            vistos.add(numero)
            texto = " ".join(palavra["text"] for palavra in linha["palavras"][1:])
            seguinte = linhas[posicao + 1] if posicao + 1 < len(linhas) else None
            if (
                seguinte is not None
                and seguinte["negrito"]
                and seguinte["tamanho"] == linha["tamanho"]
                and not RE_TITULO_NUMERADO.match(seguinte["palavras"][0]["text"])
                and seguinte["topo"] - linha["topo"] < linha["tamanho"] * 1.6
            ):
                texto = f"{texto} {seguinte['texto']}"
            titulos.append(
                {
                    "numero": numero,
                    "nivel": numero.count(".") + 1,
                    "titulo": texto.strip(),
                    "fonte_pt": linha["tamanho"],
                    "x0": linha["x0"],
                    "posicao": (indice, linha["topo"]),
                }
            )
    if not titulos:
        raise LayoutExtractionError("Nenhum título numerado ('1. INTRODUÇÃO') encontrado no corpo do laudo.")
    return titulos


def _pai(numero: str) -> str:
    return numero.rsplit(".", 1)[0]


def _titulo_antes(titulos: list[dict[str, Any]], posicao: tuple[int, float], nivel: int | None = None) -> dict[str, Any] | None:
    anteriores = [titulo for titulo in titulos if titulo["posicao"] < posicao and (nivel is None or titulo["nivel"] == nivel)]
    return anteriores[-1] if anteriores else None


def _subsecao(titulo: dict[str, Any]) -> dict[str, Any]:
    partes = RE_COMPLEMENTO_TITULO.split(titulo["titulo"], maxsplit=1)
    texto = partes[0].strip()
    subsecao: dict[str, Any] = {"numero": titulo["numero"], "titulo": texto, "chave": slug(texto)}
    if len(partes) == 3:
        # O complemento ("Recebimento Parcial com Ressalvas") é o resultado do caso.
        subsecao["complemento"] = {"separador": partes[1], "chave": slug(texto)}
    return subsecao


def _anexar_tabelas(secao: dict[str, Any], tabelas: list[dict[str, Any]]) -> None:
    """Liga as tabelas medidas à (sub)seção fixa que as contém; a chave vem da seção."""
    proprias = [tabela for tabela in tabelas if tabela["secao"] == secao["numero"]]
    for ordem, tabela in enumerate(proprias, start=1):
        tabela["chave"] = secao["chave"] if len(proprias) == 1 else f"{secao['chave']}_{ordem}"
    if proprias:
        secao["tabelas"] = [tabela["chave"] for tabela in proprias]


def _mapear_estrutura(
    titulos: list[dict[str, Any]], numero_encerramento: str | None, tabelas: list[dict[str, Any]]
) -> dict[str, Any]:
    """Espinha dorsal fixa do laudo: capítulos (nível 1) e subseções fixas (nível 2).

    Subseções de nível 2 que repetem os mesmos rótulos de nível 3 em pais
    diferentes ("Constatações", "Fundamentação Técnica") são **um sistema
    construtivo do caso** — viram laço `{% for sistema in sistemas %}`, e só os
    rótulos recorrentes são guardados. Títulos de nível 3 restantes são conteúdo
    do caso (ensaios realizados, áreas reformadas) e não entram no layout.
    """
    nivel2 = [titulo for titulo in titulos if titulo["nivel"] == 2]
    nivel3 = [titulo for titulo in titulos if titulo["nivel"] == 3]
    pais_por_rotulo: dict[str, set[str]] = {}
    for titulo in nivel3:
        pais_por_rotulo.setdefault(titulo["titulo"], set()).add(_pai(titulo["numero"]))
    recorrentes = list(dict.fromkeys(t["titulo"] for t in nivel3 if len(pais_por_rotulo[t["titulo"]]) >= 2))
    pais_dinamicos = {_pai(t["numero"]) for t in nivel3 if t["titulo"] in recorrentes}

    secoes = []
    for capitulo in (titulo for titulo in titulos if titulo["nivel"] == 1):
        filhos = [titulo for titulo in nivel2 if _pai(titulo["numero"]) == capitulo["numero"]]
        dinamicos = [titulo for titulo in filhos if titulo["numero"] in pais_dinamicos]
        if dinamicos:
            tipo = "por_sistema"
        elif RE_SECAO_FOTOGRAFICA.search(capitulo["titulo"]):
            tipo = "relatorio_fotografico"
        elif capitulo["numero"] == numero_encerramento:
            tipo = "encerramento"
        else:
            tipo = "texto"
        secao: dict[str, Any] = {
            "numero": capitulo["numero"],
            "titulo": capitulo["titulo"],
            "chave": slug(capitulo["titulo"]),
            "tipo": tipo,
            "subsecoes": [],
        }
        primeiro_dinamico = min((t["posicao"] for t in dinamicos), default=None)
        for filho in filhos:
            if filho in dinamicos:
                continue
            subsecao = _subsecao(filho)
            if primeiro_dinamico is not None:
                subsecao["posicao"] = "antes_dos_sistemas" if filho["posicao"] < primeiro_dinamico else "depois_dos_sistemas"
            secao["subsecoes"].append(subsecao)
        if dinamicos:
            secao["rotulos_por_sistema"] = [{"titulo": rotulo, "chave": slug(rotulo)} for rotulo in recorrentes]
            secao["sistemas_medidos"] = len(dinamicos)
        secoes.append(secao)

    # "Geral" existe em 2.1, 3.1 e 4.1: a chave do conteúdo precisa ser única.
    usadas = Counter(sub["chave"] for secao in secoes for sub in secao["subsecoes"])
    usadas.update(secao["chave"] for secao in secoes)
    for secao in secoes:
        for sub in secao["subsecoes"]:
            if usadas[sub["chave"]] > 1:
                sub["chave"] = f"{secao['chave']}_{sub['chave']}"
            if "complemento" in sub:
                sub["complemento"]["chave"] = sub["chave"]
    for secao in secoes:
        _anexar_tabelas(secao, tabelas)
        for sub in secao["subsecoes"]:
            _anexar_tabelas(sub, tabelas)
    return {"secoes": secoes}


def _extrair_relatorio_fotografico(
    pdf: Any, indices: list[int], linhas_por_pagina: dict[int, list[dict[str, Any]]], largura_pt: float
) -> dict[str, Any]:
    """Grade de fotos (fotos por página, caixa da foto) e estilo da legenda 'Figura N'."""
    contagem: list[int] = []
    caixas: list[tuple[int, int]] = []
    xs: list[int] = []
    legendas: list[dict[str, Any]] = []
    afastamentos: list[int] = []
    separadores: list[str] = []
    fontes_legenda: list[str] = []
    for indice in indices:
        pagina = pdf.pages[indice]
        fotos = _fotos(pagina)
        if not fotos:
            continue
        contagem.append(len(fotos))
        for foto in fotos:
            caixas.append((round(float(foto["width"])), round(float(foto["height"]))))
            xs.append(round(float(foto["x0"])))
        linhas = linhas_por_pagina[indice]
        for posicao, linha in enumerate(linhas):
            if not RE_LEGENDA_FIGURA.match(linha["texto"]):
                continue
            legendas.append(linha)
            separador = RE_SEPARADOR_LEGENDA.match(linha["texto"])
            if separador:
                separadores.append(separador.group(1))
            acima = [foto for foto in fotos if float(foto["bottom"]) <= linha["topo"] + 1]
            if acima:
                afastamentos.append(round(linha["topo"] - max(float(foto["bottom"]) for foto in acima)))
            # A legenda continua nas linhas seguintes de mesmo estilo; o sufixo
            # "Fonte: Autor." é rótulo fixo, o resto é a descrição do caso.
            texto = linha["texto"]
            for seguinte in linhas[posicao + 1 :]:
                if RE_LEGENDA_FIGURA.match(seguinte["texto"]) or seguinte["tamanho"] != linha["tamanho"]:
                    break
                texto = f"{texto} {seguinte['texto']}"
            sufixo = RE_FONTE_LEGENDA.search(texto)
            if sufixo:
                fontes_legenda.append(re.sub(r"\s+", " ", sufixo.group(1)))
    if not contagem:
        raise LayoutExtractionError(
            "Nenhuma página com fotos encontrada no PDF — o relatório fotográfico é obrigatório na vistoria cautelar."
        )
    largura, altura = _moda(caixas)
    x_foto = _moda(xs)
    return {
        "fotos_por_pagina": _moda(contagem),
        "foto": {
            "largura_pt": float(largura),
            "altura_pt": float(altura),
            "x_pt": float(x_foto),
            "alinhamento": _alinhamento(x_foto, x_foto + largura, largura_pt),
        },
        "legenda": {
            "rotulo": "Figura",
            "separador": _moda(separadores, "-"),
            "posicao": "abaixo" if afastamentos else "indefinida",
            "afastamento_pt": float(_moda(afastamentos, 0)),
            "familia": _familia_legivel(_moda([linha["fonte"] for linha in legendas], "")) if legendas else None,
            "fonte_pt": _moda([linha["tamanho"] for linha in legendas]),
            "italico": _moda([linha["italico"] for linha in legendas], False),
            "cor": _moda([linha["cor"] for linha in legendas]),
            "sufixo_fonte": _moda(fontes_legenda),
        },
        "paginas_medidas": len(contagem),
    }


def _cabecalho_de_tabela(pagina: Any) -> dict[str, Any] | None:
    """Linha de cabeçalho preenchida mais alta da página: colunas, larguras e cores."""
    preenchidos = []
    for retangulo in pagina.rects:
        cor = _cor_hex(retangulo.get("non_stroking_color"))
        if cor in (None, "#FFFFFF", "#000000") or not 6 <= float(retangulo["height"]) <= 40:
            continue
        preenchidos.append((round(float(retangulo["top"])), cor, retangulo))
    grupos: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for topo, cor, retangulo in preenchidos:
        grupos.setdefault((topo, cor), []).append(retangulo)
    # Realce de texto (marca-texto numa legenda) também é retângulo preenchido:
    # cabeçalho de tabela de verdade ocupa boa parte da largura da página.
    candidatos = sorted(
        chave
        for chave, grupo in grupos.items()
        if max(float(r["x1"]) for r in grupo) - min(float(r["x0"]) for r in grupo)
        >= float(pagina.width) * FRACAO_LARGURA_TABELA
    )
    if not candidatos:
        return None
    topo_cabecalho, cor = candidatos[0]
    linha_cabecalho = grupos[(topo_cabecalho, cor)]
    # Cada célula pode vir como retângulo externo + interno (padding); fica o externo.
    externos = sorted(
        (
            r
            for r in linha_cabecalho
            if not any(
                o is not r and o["x0"] <= r["x0"] and o["x1"] >= r["x1"] and (o["x1"] - o["x0"]) > (r["x1"] - r["x0"])
                for o in linha_cabecalho
            )
        ),
        key=lambda r: r["x0"],
    )
    palavras = pagina.extract_words(extra_attrs=["size", "fontname", "non_stroking_color"])
    largura_total = float(externos[-1]["x1"]) - float(externos[0]["x0"])
    if largura_total <= 0:
        return None
    colunas = []
    cabecalho_palavras = []
    for celula in externos:
        dentro = [
            p
            for p in palavras
            if celula["x0"] <= (p["x0"] + p["x1"]) / 2 <= celula["x1"]
            and celula["top"] - 2 <= p["top"] <= celula["bottom"] + 2
        ]
        rotulo = " ".join(p["text"] for p in sorted(dentro, key=lambda p: (round(p["top"]), p["x0"])))
        cabecalho_palavras += dentro
        colunas.append(
            {
                "rotulo": rotulo,
                "chave": slug(rotulo),
                "largura_pct": round((float(celula["x1"]) - float(celula["x0"])) / largura_total * 100, 1),
            }
        )
    if not cabecalho_palavras:
        return None
    base = max(float(r["bottom"]) for r in externos)
    corpo = [
        p
        for p in palavras
        if base + 1 < p["top"] < float(pagina.height) * FRACAO_RODAPE
        and float(externos[0]["x0"]) <= p["x0"] <= float(externos[-1]["x1"])
    ][:200]
    return {
        "topo_pt": float(topo_cabecalho),
        "colunas": colunas,
        "cabecalho_fundo": cor,
        "cabecalho_cor_texto": _moda([_cor_hex(p["non_stroking_color"]) for p in cabecalho_palavras]),
        "cabecalho_fonte_pt": _moda([round(float(p["size"]), 1) for p in cabecalho_palavras]),
        "cabecalho_negrito": _moda([_e_negrito(p["fontname"]) for p in cabecalho_palavras], True),
        "familia": _familia_legivel(_moda([_familia(p["fontname"]) for p in cabecalho_palavras])),
        "corpo_fonte_pt": _moda([round(float(p["size"]), 1) for p in corpo]),
        "x_pt": round(float(externos[0]["x0"]), 1),
        "largura_pt": round(largura_total, 1),
    }


def _extrair_tabelas(pdf: Any, indices: list[int], titulos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Tabelas distintas (pelo cabeçalho), na ordem, ancoradas no título que as precede.

    Só o cabeçalho é rótulo fixo; as células do corpo são conteúdo do caso e não
    são lidas. Um cabeçalho repetido na página seguinte (tabela que quebra) é a
    mesma tabela.
    """
    tabelas: list[dict[str, Any]] = []
    vistos: set[tuple[str, ...]] = set()
    for indice in indices:
        cabecalho = _cabecalho_de_tabela(pdf.pages[indice])
        if cabecalho is None:
            continue
        assinatura = tuple(coluna["chave"] for coluna in cabecalho["colunas"])
        if assinatura in vistos:
            continue
        vistos.add(assinatura)
        anterior = _titulo_antes(titulos, (indice, cabecalho.pop("topo_pt")))
        # Títulos de nível 3+ são conteúdo do caso: a tabela sobe para o nível 2.
        numero = ".".join(anterior["numero"].split(".")[:2]) if anterior else None
        tabelas.append({"secao": numero, "chave": f"tabela_{len(tabelas) + 1}", **cabecalho})
    return tabelas


def _extrair_assinatura(
    pdf: Any, indices: list[int], linhas_por_pagina: dict[int, list[dict[str, Any]]], largura_pt: float, altura_pt: float
) -> dict[str, Any] | None:
    """Bloco de assinatura (última linha '_____'): geometria, e texto trocado por placeholders."""
    limite = altura_pt * FRACAO_RODAPE
    for indice in reversed(indices):
        linhas = [linha for linha in linhas_por_pagina[indice] if linha["topo"] < limite]
        posicao = next((p for p in range(len(linhas) - 1, -1, -1) if RE_LINHA_ASSINATURA.match(linhas[p]["texto"])), None)
        if posicao is None:
            continue
        traco = linhas[posicao]
        abaixo = linhas[posicao + 1 :]
        modelos: list[str] = []
        data = None
        qualificacoes = 0
        anterior = traco
        for linha in abaixo:
            if RE_DATA_EXTENSO.search(linha["texto"]):
                data = linha
                break
            if linha["topo"] - anterior["topo"] > linha["tamanho"] * 3:
                break
            anterior = linha
            if not modelos:
                modelos.append(PH_NOME)
            elif RE_CREA.search(linha["texto"]) and PH_REGISTRO not in modelos:
                modelos.append(PH_REGISTRO)
            else:
                qualificacoes += 1
        nome = abaixo[0] if abaixo else traco
        imagem = next(
            (
                img
                for img in pdf.pages[indice].images
                # A rubrica costuma cruzar o traço: basta sobrepor a faixa de ±60 pt.
                if float(img["top"]) <= traco["topo"] + 60
                and float(img["bottom"]) >= traco["topo"] - 60
                and float(img["x1"]) > traco["x0"]
                and float(img["x0"]) < traco["x1"]
                and img not in _imagens_de_cabecalho(pdf.pages[indice])
            ),
            None,
        )
        return {
            "posicao": (indice, traco["topo"]),
            "alinhamento": _alinhamento(traco["x0"], traco["x1"], largura_pt, margem_direita_pt=traco["x1"]),
            "familia": _familia_legivel(nome["fonte"]),
            "fonte_pt": nome["tamanho"],
            "nome_negrito": nome["negrito"],
            "linha_largura_pt": round(traco["x1"] - traco["x0"], 1),
            "linhas": modelos,
            "qualificacoes": {"modelo": "{% for linha in responsavel.qualificacoes %}", "linhas_medidas": qualificacoes},
            "imagem_assinatura": _caixa(imagem) if imagem else None,
            "local_data": (
                {
                    "modelo": PH_LOCAL_DATA,
                    "afastamento_pt": round(data["topo"] - anterior["topo"], 1),
                    "alinhamento": _alinhamento(data["x0"], data["x1"], largura_pt, margem_direita_pt=traco["x1"]),
                }
                if data
                else None
            ),
        }
    return None


def _cor_do_texto(paginas_texto: list[Any], altura_pt: float) -> str:
    limite = altura_pt * FRACAO_RODAPE
    cores = [
        _cor_hex(caractere.get("non_stroking_color"))
        for pagina in paginas_texto
        for caractere in pagina.chars[:3000]
        if float(caractere["top"]) < limite
    ]
    return _moda([cor for cor in cores if cor], "#000000")


def _garantir_sem_dados_pessoais(valor: Any, caminho: str = "layout") -> None:
    """Falha (sem ecoar o valor) se sobrar dado pessoal em qualquer string do layout."""
    if isinstance(valor, dict):
        for chave, item in valor.items():
            if chave == "origem":
                continue  # hash do arquivo: hexadecimal, não é dado pessoal
            _garantir_sem_dados_pessoais(item, f"{caminho}.{chave}")
    elif isinstance(valor, (list, tuple)):
        for posicao, item in enumerate(valor):
            _garantir_sem_dados_pessoais(item, f"{caminho}[{posicao}]")
    elif isinstance(valor, str):
        if RE_COR_HEX.fullmatch(valor):
            return
        for detector in (RE_EMAIL, RE_TELEFONE, RE_CPF, RE_CEP, RE_NUMERO_LONGO):
            if detector.search(valor):
                raise LayoutExtractionError(
                    f"Dado pessoal detectado em {caminho} — o layout.json é versionado e não pode carregá-lo (A02)."
                )


def extrair_layout(caminho_pdf: Path, *, pagina_inicial_corpo: int | None = None) -> dict[str, Any]:
    """Lê o PDF final da vistoria cautelar e devolve a especificação de layout.

    `pagina_inicial_corpo` (índice 0-based) força o início do corpo; sem ele, o
    corpo começa na página seguinte ao último sumário detectado.
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
        linhas_por_pagina = {indice: _linhas(pagina) for indice, pagina in enumerate(pdf.pages)}

        indices_sumario = [i for i in range(1, len(pdf.pages)) if _e_pagina_de_sumario(linhas_por_pagina[i])]
        if pagina_inicial_corpo is None:
            pagina_inicial_corpo = (max(indices_sumario) + 1) if indices_sumario else 1
        indices_corpo = [i for i in range(pagina_inicial_corpo, len(pdf.pages)) if i not in indices_sumario]
        if not indices_corpo:
            raise LayoutExtractionError("O PDF não tem páginas de corpo após o sumário.")
        indices_texto = [i for i in indices_corpo if not _fotos(pdf.pages[i]) and linhas_por_pagina[i]]
        if not indices_texto:
            raise LayoutExtractionError("Nenhuma página de texto corrido encontrada para medir o layout.")
        paginas_texto = [pdf.pages[i] for i in indices_texto]

        tipografia = _extrair_tipografia(paginas_texto, altura_pt)
        cabecalho = _extrair_cabecalho([pdf.pages[i] for i in indices_corpo], largura_pt)
        rodape = _extrair_rodape([(i, linhas_por_pagina[i]) for i in indices_corpo], largura_pt, altura_pt)
        margens, paragrafo = _extrair_pagina_e_paragrafo(
            [linhas_por_pagina[i] for i in indices_texto],
            tipografia,
            largura_pt,
            altura_pt,
            rodape["topo_pt"],
            cabecalho["base_pt"],
        )
        margem_esquerda_pt = margens["esquerda"] / PONTO_EM_CM

        titulos = _extrair_titulos([(i, linhas_por_pagina[i]) for i in indices_corpo], tipografia, altura_pt)
        tabelas = _extrair_tabelas(pdf, indices_corpo, titulos)
        assinatura = _extrair_assinatura(pdf, indices_corpo, linhas_por_pagina, largura_pt, altura_pt)
        capitulo_assinatura = _titulo_antes(titulos, assinatura["posicao"], nivel=1) if assinatura else None
        estrutura = _mapear_estrutura(titulos, capitulo_assinatura["numero"] if capitulo_assinatura else None, tabelas)
        if assinatura:
            assinatura.pop("posicao")

        niveis: dict[int, list[dict[str, Any]]] = {}
        for titulo in titulos:
            niveis.setdefault(titulo["nivel"], []).append(titulo)
        hierarquia = [
            {
                "nivel": nivel,
                "fonte_pt": _moda([t["fonte_pt"] for t in itens]),
                "negrito": True,
                "recuo_cm": _cm(_moda([round(t["x0"]) for t in itens]) - margem_esquerda_pt),
            }
            for nivel, itens in sorted(niveis.items())
        ]

        relatorio = _extrair_relatorio_fotografico(pdf, indices_corpo, linhas_por_pagina, largura_pt)
        capa = _extrair_capa(primeira, linhas_por_pagina[0], largura_pt)
        primeiro_sumario = min(indices_sumario) if indices_sumario else pagina_inicial_corpo
        folha_de_rosto = (
            _extrair_folha_de_rosto(linhas_por_pagina[1], largura_pt, altura_pt) if primeiro_sumario > 1 else None
        )
        sumario = _extrair_sumario([linhas_por_pagina[i] for i in indices_sumario], margem_esquerda_pt)

        cores = {
            "texto": _cor_do_texto(paginas_texto, altura_pt),
            "legenda": relatorio["legenda"]["cor"],
            "rodape_contato": next(
                (linha["cor"] for linha in rodape["linhas"] if linha["modelo"] == PH_CONTATO), None
            ),
            "capa_titulo": capa["titulo"]["cor"],
            "capa_destaque": next(
                (elemento["cor"] for elemento in capa["elementos"] if elemento["papel"] == "responsavel"), None
            ),
            "tabela_cabecalho_fundo": [tabela["cabecalho_fundo"] for tabela in tabelas],
        }

        e_a4 = abs(largura_pt - A4_LARGURA_PT) < TOLERANCIA_A4_PT and abs(altura_pt - A4_ALTURA_PT) < TOLERANCIA_A4_PT
        layout = {
            "versao_schema": 1,
            "tipo_documento": TIPO_DOCUMENTO,
            "origem": {
                # Só o hash: o nome do arquivo identifica o cliente ("Reforma <cond.>").
                "sha256": _sha256(caminho_pdf),
                "paginas": len(pdf.pages),
            },
            "pagina": {
                "tamanho": "A4" if e_a4 else f"{largura_pt}x{altura_pt}pt",
                "orientacao": "portrait" if altura_pt >= largura_pt else "landscape",
                "largura_pt": largura_pt,
                "altura_pt": altura_pt,
                "margens_cm": margens,
            },
            "tipografia": tipografia,
            "paragrafo": paragrafo,
            "titulos": hierarquia,
            "cores": cores,
            "capa": capa,
            "folha_de_rosto": folha_de_rosto,
            "sumario": sumario,
            "cabecalho": cabecalho,
            "rodape": rodape,
            "estrutura": estrutura,
            "relatorio_fotografico": relatorio,
            "tabelas": tabelas,
            "assinatura": assinatura,
        }
    _garantir_sem_dados_pessoais(layout)
    return layout
