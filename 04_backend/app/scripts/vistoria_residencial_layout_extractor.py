"""Extração determinística do layout da Vistoria de Imóvel Residencial a partir do PDF final.

Fatia "Vistoria Residencial" de ADR-13/DEC-25 (`00_docs/arquitetura.md`), pelo
mesmo método do LTIP (BL-17, `ltip_layout_extractor`): as métricas são
**medidas** com `pdfplumber` no PDF final do cliente e gravadas em
`templates/vistoria_residencial/layout.json`, do qual derivam o `.html.j2` do
WeasyPrint e o `.docx` do docxtpl (RF-06) — os dois formatos saem da mesma
especificação.

O que este laudo tem de diferente do LTIP, e por isso é medido aqui:

- cabeçalho com a logo em **todas** as páginas (não só na capa);
- folha de rosto depois da capa, com o título do laudo em bloco;
- relatório fotográfico em **figuras numeradas com legenda** (não em fichas GUT);
- capítulo de análise **por sistema**, com subtítulos fixos marcados ("Constatações",
  "Fundamentação Técnica");
- bloco de assinatura do responsável técnico no encerramento.

Privacidade (OWASP A02): o `layout.json` é versionado, então guarda **apenas
geometria e rótulos fixos**. Rodapé, capa, folha de rosto e assinatura do exemplar
trazem nome, CREA, e-mail, telefone, número do apartamento e nome do
empreendimento — tudo isso vira placeholder Jinja2 nomeado (`{{ fiscal.nome }}`,
`{{ imovel.unidade }}`...). Os únicos textos copiados do original são títulos de
seção e de capa, e ainda assim passam por `anonimizar()`; no fim,
`verificar_sem_dados_pessoais()` recusa gravar se algum padrão de dado pessoal
sobrou.

O original fica em `01_output-context/`, fora do Git; o caminho é sempre recebido
por parâmetro e a ausência do arquivo falha explicitamente.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from itertools import pairwise
from pathlib import Path
from typing import Any

import pdfplumber

# Reaproveitado do LTIP por import (sem editar aquele módulo): mesma normalização
# de fonte, mesma capa (título de maior corpo + logo no topo), mesma hierarquia de
# títulos numerados e mesmo hash de procedência.
from app.scripts.ltip_layout_extractor import (
    A4_ALTURA_PT,
    A4_LARGURA_PT,
    PONTO_EM_CM,
    RE_LEGENDA_FIGURA,
    RE_TITULO_NUMERADO,
    TOLERANCIA_A4_PT,
    LayoutExtractionError,
    _e_negrito,
    _extrair_capa,
    _extrair_hierarquia_de_titulos,
    _familia,
    _familia_legivel,
    _sha256,
)

TIPO_DOCUMENTO = "VISTORIA_RESIDENCIAL"

#: Capítulo cujo conteúdo são as figuras numeradas do relatório fotográfico.
RE_CAPITULO_FOTOGRAFICO = re.compile(r"RELAT[ÓO]RIO\s+FOTOGR", re.IGNORECASE)
#: Capítulo cujas subseções são os sistemas inspecionados daquele caso — os
#: títulos das subseções são conteúdo do caso e viram laço no template.
RE_CAPITULO_POR_SISTEMA = re.compile(r"AN[ÁA]LISE\s+E\s+CONSIDERA", re.IGNORECASE)
#: Marcadores dos subtítulos fixos da análise por sistema ("➢ Constatações").
MARCADORES_SUBTITULO = "➢►>▪•"
#: Linha de assinatura ("________________").
RE_LINHA_ASSINATURA = re.compile(r"^_{10,}$")
#: Local e data do encerramento ("<cidade>, 11 de maio de 2026.").
RE_LOCAL_DATA = re.compile(r"\d{1,2}\s+de\s+\w+\s+de\s+\d{4}", re.IGNORECASE)
#: Sufixo de fonte das legendas ("Fonte: Autor.").
RE_FONTE_LEGENDA = re.compile(r"Fonte:\s*([^.]+)\.?\s*$")
#: Separador entre "Figura N" e a descrição.
#: Hífen, meia-risca (U+2013), travessão (U+2014) ou dois-pontos.
RE_SEPARADOR_LEGENDA = re.compile(r"^figura\s+\d+\s*([-\u2013\u2014:])", re.IGNORECASE)
#: Rótulo fixo da capa antes do nome do responsável.
RE_ROTULO_RESPONSAVEL = re.compile(r"^RESP\.?\s*T[ÉE]CNICO\s*:?", re.IGNORECASE)

#: Papéis das linhas do rodapé e o placeholder que substitui o texto do exemplar.
PLACEHOLDER_RODAPE = {
    "nome": "{{ fiscal.nome }}",
    "registro": "Eng. Civil - CREA nº {{ fiscal.crea }}",
    "contato": "{{ fiscal.email }} / {{ fiscal.telefone }}",
}

#: Substituições de `anonimizar()`, na ordem em que são aplicadas.
_SUBSTITUICOES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+"), "{{ fiscal.email }}"),
    (re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}"), "{{ contratante.cpf_cnpj }}"),
    (re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"), "{{ contratante.cpf_cnpj }}"),
    (re.compile(r"CREA[-\w]*\s*(n[º°o]\.?|:)?\s*[\d][\d./-]*\s*[-/]?\s*[A-Z]?(-?[A-Z]{2})?"), "CREA nº {{ fiscal.crea }}"),
    (re.compile(r"\(?\b\d{2}\)?\s*9?\s*\d{4}-?\d{4}\b"), "{{ fiscal.telefone }}"),
    (re.compile(r"\b\d{5}-\d{3}\b"), "{{ edificacao.cep }}"),
    (re.compile(r"\b(Ap(to)?\.?|Apartamento|Unidade)\s*n?[º°]?\s*\d+[A-Z]?\b", re.IGNORECASE), "{{ imovel.unidade }}"),
)

#: Padrões que não podem sobrar no layout serializado (guarda final, A02).
_PADROES_PROIBIDOS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}"),
    re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"),
    re.compile(r"\(?\b\d{2}\)?\s*9?\s*\d{4}-\d{4}\b"),
    re.compile(r"CREA[^{}\n]{0,12}\d{5,}"),
    re.compile(r"\b(Ap(to)?\.|Apartamento)\s*\d+", re.IGNORECASE),
    re.compile(r"\b\d{5}-\d{3}\b"),
)


def anonimizar(texto: str) -> str:
    """Troca por placeholder Jinja2 qualquer dado pessoal reconhecível num texto fixo."""
    for padrao, placeholder in _SUBSTITUICOES:
        texto = padrao.sub(placeholder, texto)
    return texto


def verificar_sem_dados_pessoais(layout: dict[str, Any]) -> None:
    """Recusa o layout se sobrou e-mail, CPF/CNPJ, telefone, CREA, CEP ou nº de unidade.

    `origem` fica de fora: guarda só o sha256 e a contagem de páginas.
    """
    sem_origem = {chave: valor for chave, valor in layout.items() if chave != "origem"}
    serializado = json.dumps(sem_origem, ensure_ascii=False)
    for padrao in _PADROES_PROIBIDOS:
        achado = padrao.search(serializado)
        if achado:
            raise LayoutExtractionError(
                "O layout extraído ainda contém um dado do exemplar (padrão "
                f"{padrao.pattern!r}). Nada foi gravado: ajuste anonimizar() antes de versionar."
            )


def slug(texto: str) -> str:
    """`Fundamentação Técnica` -> `fundamentacao_tecnica` (chave estável de contexto)."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")


def _cor_hex(cor: Any) -> str:
    """Cor de preenchimento do pdfplumber (cinza, RGB ou CMYK) em hexadecimal."""
    if cor is None:
        return "#000000"
    if isinstance(cor, (int, float)):
        cor = (cor,)
    try:
        valores = tuple(float(componente) for componente in cor)
    except (TypeError, ValueError):
        return "#000000"
    if len(valores) == 1:
        vermelho = verde = azul = valores[0]
    elif len(valores) == 3:
        vermelho, verde, azul = valores
    elif len(valores) == 4:
        ciano, magenta, amarelo, preto = valores
        vermelho, verde, azul = ((1 - ciano) * (1 - preto), (1 - magenta) * (1 - preto), (1 - amarelo) * (1 - preto))
    else:
        return "#000000"
    return "#" + "".join(f"{round(max(0.0, min(1.0, canal)) * 255):02X}" for canal in (vermelho, verde, azul))


def _cor_do_caractere(caractere: dict[str, Any]) -> str:
    return _cor_hex(caractere.get("non_stroking_color"))


def _linhas(pagina: Any) -> list[dict[str, Any]]:
    """Palavras agrupadas por linha (topo arredondado), na ordem de leitura."""
    agrupadas: dict[int, list[dict[str, Any]]] = {}
    for palavra in pagina.extract_words(extra_attrs=["size", "fontname"]):
        agrupadas.setdefault(round(float(palavra["top"])), []).append(palavra)
    linhas = []
    for topo in sorted(agrupadas):
        palavras = sorted(agrupadas[topo], key=lambda item: item["x0"])
        linhas.append(
            {
                "top": float(topo),
                "bottom": max(float(palavra["bottom"]) for palavra in palavras),
                "x0": min(float(palavra["x0"]) for palavra in palavras),
                "x1": max(float(palavra["x1"]) for palavra in palavras),
                "texto": " ".join(palavra["text"] for palavra in palavras),
                "fontname": palavras[0]["fontname"],
                "size": round(float(palavras[0]["size"]), 1),
                "negrito": all(_e_negrito(palavra["fontname"]) for palavra in palavras),
                "palavras": palavras,
            }
        )
    return linhas


def _e_a4(pagina: Any) -> bool:
    largura, altura = float(pagina.width), float(pagina.height)
    retrato = abs(largura - A4_LARGURA_PT) < TOLERANCIA_A4_PT and abs(altura - A4_ALTURA_PT) < TOLERANCIA_A4_PT
    return retrato


def _imagens_de_cabecalho(pagina: Any) -> list[dict[str, Any]]:
    """Imagens pequenas na faixa superior da página — a logo do cabeçalho."""
    altura, largura = float(pagina.height), float(pagina.width)
    return [
        imagem
        for imagem in pagina.images
        if float(imagem["top"]) < altura * 0.1 and float(imagem["width"]) < largura * 0.4
    ]


def _imagens_de_conteudo(pagina: Any) -> list[dict[str, Any]]:
    cabecalho = _imagens_de_cabecalho(pagina)
    return [imagem for imagem in pagina.images if imagem not in cabecalho]


def _extrair_cabecalho(paginas: list[Any]) -> dict[str, Any]:
    """Caixa da logo repetida no cabeçalho das páginas internas (moda da posição)."""
    caixas = Counter()
    for pagina in paginas:
        for imagem in _imagens_de_cabecalho(pagina):
            caixas[
                (
                    round(float(imagem["x0"]), 1),
                    round(float(imagem["top"]), 1),
                    round(float(imagem["width"]), 1),
                    round(float(imagem["height"]), 1),
                )
            ] += 1
    if not caixas:
        return {"logo": None, "paginas_com_logo": 0}
    (x0, topo, largura, altura), quantidade = caixas.most_common(1)[0]
    largura_pagina = float(paginas[0].width)
    centro = x0 + largura / 2
    alinhamento = "direita" if centro > largura_pagina * 0.6 else "esquerda" if centro < largura_pagina * 0.4 else "centro"
    return {
        "logo": {
            "x_pt": x0,
            "topo_pt": topo,
            "largura_pt": largura,
            "altura_pt": altura,
            "alinhamento": alinhamento,
        },
        "paginas_com_logo": quantidade,
    }


def _papel_da_linha_de_rodape(texto: str) -> str:
    if "@" in texto:
        return "contato"
    if re.search(r"CREA", texto, re.IGNORECASE):
        return "registro"
    return "nome"


def _extrair_rodape(paginas: list[Any], cor_texto: str, corpo_pt: float) -> dict[str, Any]:
    """Estrutura do rodapé: papéis das linhas (viram placeholder), corpo, cor do link e numeração.

    Só conta como rodapé a linha na faixa inferior com corpo **menor** que o do
    texto — parágrafo que escorre até o pé da página não é rodapé. A sequência de
    papéis é a moda por página, não por posição.
    """
    sequencias = Counter()
    fontes = Counter()
    cores_link = Counter()
    topos = Counter()
    numeracao = Counter()
    for pagina in paginas:
        altura, largura = float(pagina.height), float(pagina.width)
        linhas = [
            linha for linha in _linhas(pagina) if linha["top"] >= altura * 0.9 and linha["size"] < corpo_pt
        ]
        textuais = [linha for linha in linhas if not linha["texto"].strip().isdigit()]
        sequencias[tuple(_papel_da_linha_de_rodape(linha["texto"]) for linha in textuais)] += 1
        for posicao, linha in enumerate(textuais):
            fontes[(_familia(linha["fontname"]), linha["size"])] += 1
            if posicao == 0:
                topos[round(linha["top"], 1)] += 1
        for linha in textuais:
            if _papel_da_linha_de_rodape(linha["texto"]) != "contato":
                continue
            cores = Counter(
                _cor_do_caractere(caractere)
                for caractere in pagina.chars
                if linha["top"] - 1 <= float(caractere["top"]) <= linha["bottom"] + 1
            )
            for cor, _ in cores.most_common():
                if cor != cor_texto:
                    cores_link[cor] += 1
                    break
        for linha in linhas:
            if linha["texto"].strip().isdigit():
                centro = (linha["x0"] + linha["x1"]) / 2
                posicao_numero = (
                    "direita" if centro > largura * 0.6 else "esquerda" if centro < largura * 0.4 else "centro"
                )
                numeracao[(posicao_numero, _familia_legivel(linha["fontname"]), linha["size"])] += 1

    papeis_ordenados = list(sequencias.most_common(1)[0][0]) if sequencias else []
    fonte_rodape = fontes.most_common(1)[0][0] if fontes else (None, None)
    numero = numeracao.most_common(1)[0][0] if numeracao else None
    return {
        "papeis": papeis_ordenados,
        "linhas": [PLACEHOLDER_RODAPE[papel] for papel in papeis_ordenados],
        "familia": _familia_legivel(fonte_rodape[0]) if fonte_rodape[0] else None,
        "fonte_pt": fonte_rodape[1],
        "alinhamento": "centro",
        "cor_link": cores_link.most_common(1)[0][0] if cores_link else None,
        "topo_pt": topos.most_common(1)[0][0] if topos else None,
        "numeracao_pagina": (
            {"alinhamento": numero[0], "familia": numero[1], "fonte_pt": numero[2]} if numero else None
        ),
    }


def _extrair_tipografia_e_margens(paginas: list[Any], rodape_topo_pt: float | None) -> dict[str, Any]:
    """Corpo de texto pela moda de fonte/corpo; margens pela moda das bordas das linhas de corpo.

    Diferente do LTIP, a margem esquerda não é a borda mínima da página: os
    títulos de capítulo deste laudo às vezes recuam ~1 cm à esquerda do texto, e
    uma lista com marcador mais ainda — a moda das linhas de corpo é o bloco real.
    """
    corpo = Counter()
    cores = Counter()
    for pagina in paginas:
        limite = float(pagina.height) * 0.9
        for caractere in pagina.chars:
            if float(caractere["top"]) >= limite:
                continue
            corpo[(_familia(caractere["fontname"]), round(float(caractere["size"]), 1))] += 1
    if not corpo:
        raise LayoutExtractionError("Nenhum texto de corpo encontrado nas páginas internas.")
    (fonte_corpo, tamanho_corpo), _ = corpo.most_common(1)[0]

    esquerda, direita, topo = Counter(), Counter(), Counter()
    for pagina in paginas:
        limite = float(pagina.height) * 0.9
        linhas = [linha for linha in _linhas(pagina) if linha["top"] < limite]
        for linha in linhas:
            if _familia(linha["fontname"]) == fonte_corpo and linha["size"] == tamanho_corpo:
                esquerda[round(linha["x0"])] += 1
                direita[round(linha["x1"])] += 1
        if linhas:
            topo[round(min(linha["top"] for linha in linhas))] += 1
        for caractere in pagina.chars:
            if float(caractere["top"]) < limite and _familia(caractere["fontname"]) == fonte_corpo:
                cores[_cor_do_caractere(caractere)] += 1

    largura = float(paginas[0].width)
    altura = float(paginas[0].height)
    inferior = altura - (rodape_topo_pt if rodape_topo_pt else altura)
    return {
        "tipografia": {
            "familia": _familia_legivel(fonte_corpo),
            "familia_postscript": fonte_corpo,
            "corpo_pt": tamanho_corpo,
        },
        "cor_texto": cores.most_common(1)[0][0] if cores else "#000000",
        "margens_cm": {
            "esquerda": round(esquerda.most_common(1)[0][0] * PONTO_EM_CM, 2),
            "direita": round((largura - direita.most_common(1)[0][0]) * PONTO_EM_CM, 2),
            "superior": round(topo.most_common(1)[0][0] * PONTO_EM_CM, 2),
            "inferior": round(inferior * PONTO_EM_CM, 2),
        },
    }


def _extrair_secoes(paginas: list[tuple[int, Any]], corpo_pt: float) -> list[dict[str, Any]]:
    """Títulos numerados do corpo, na ordem do documento, com o índice da página.

    Título = linha cuja primeira palavra é `N.`/`N.N.` em negrito e com corpo
    igual ou maior que o do texto (níveis 3+ usam 12pt negrito; o sumário usa
    negrito menor e, além disso, fica antes de `pagina_inicial_corpo`).
    """
    secoes: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for indice, pagina in paginas:
        for linha in _linhas(pagina):
            primeira = linha["palavras"][0]
            numero = primeira["text"]
            if not RE_TITULO_NUMERADO.match(numero) or not _e_negrito(primeira["fontname"]):
                continue
            if round(float(primeira["size"]), 1) < corpo_pt or numero in vistos:
                continue
            titulo = " ".join(palavra["text"] for palavra in linha["palavras"][1:]).strip()
            if not titulo:
                continue
            vistos.add(numero)
            secoes.append(
                {
                    "numero": numero,
                    "nivel": numero.rstrip(".").count(".") + 1,
                    "titulo": titulo,
                    "_pagina": indice,
                }
            )
    return secoes


def _classificar_secoes(secoes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Marca os capítulos especiais e descarta as subseções que são conteúdo do caso."""
    resultado: list[dict[str, Any]] = []
    capitulo_dinamico: str | None = None
    for secao in secoes:
        if secao["nivel"] == 1:
            capitulo_dinamico = None
            tipo = "texto"
            if RE_CAPITULO_FOTOGRAFICO.search(secao["titulo"]):
                tipo = "fotografico"
                capitulo_dinamico = secao["numero"]
            elif RE_CAPITULO_POR_SISTEMA.search(secao["titulo"]):
                tipo = "por_sistema"
                capitulo_dinamico = secao["numero"]
            resultado.append({**secao, "tipo": tipo})
            continue
        if capitulo_dinamico and secao["numero"].startswith(capitulo_dinamico):
            continue
        resultado.append({**secao, "tipo": "texto"})
    return resultado


def _intervalo_do_capitulo(secoes: list[dict[str, Any]], tipo: str, total_paginas: int) -> range | None:
    capitulos = [secao for secao in secoes if secao["nivel"] == 1]
    for posicao, capitulo in enumerate(capitulos):
        if capitulo["tipo"] != tipo:
            continue
        fim = capitulos[posicao + 1]["_pagina"] if posicao + 1 < len(capitulos) else total_paginas
        return range(capitulo["_pagina"], max(fim, capitulo["_pagina"] + 1))
    return None


def _extrair_relatorio_fotografico(pdf: pdfplumber.PDF, intervalo: range | None) -> dict[str, Any]:
    """Grade de fotos e formato da legenda ("Figura N - descrição. Fonte: Autor.")."""
    if intervalo is None:
        raise LayoutExtractionError(
            "Capítulo 'RELATÓRIO FOTOGRÁFICO' não encontrado — ele é obrigatório na Vistoria Residencial."
        )
    por_pagina, colunas, tamanhos = Counter(), Counter(), Counter()
    fontes_legenda, cores_legenda, separadores, fontes_citadas = Counter(), Counter(), Counter(), Counter()
    legenda_abaixo = Counter()
    for indice in intervalo:
        pagina = pdf.pages[indice]
        largura = float(pagina.width)
        fotos = [imagem for imagem in _imagens_de_conteudo(pagina) if float(imagem["width"]) > largura * 0.3]
        legendas = [linha for linha in _linhas(pagina) if RE_LEGENDA_FIGURA.match(linha["texto"])]
        if fotos:
            por_pagina[len(fotos)] += 1
            colunas[len({round(float(foto["x0"])) for foto in fotos})] += 1
            for foto in fotos:
                tamanhos[(round(float(foto["width"]), 1), round(float(foto["height"]), 1))] += 1
        for legenda in legendas:
            fontes_legenda[(legenda["fontname"], legenda["size"])] += 1
            separador = RE_SEPARADOR_LEGENDA.match(legenda["texto"])
            if separador:
                separadores[separador.group(1)] += 1
            citada = RE_FONTE_LEGENDA.search(legenda["texto"])
            if citada:
                fontes_citadas[citada.group(1).strip()] += 1
            for caractere in pagina.chars:
                if legenda["top"] - 1 <= float(caractere["top"]) <= legenda["bottom"] + 1:
                    cores_legenda[_cor_do_caractere(caractere)] += 1
            acima = [foto for foto in fotos if float(foto["bottom"]) <= legenda["top"] + 2]
            legenda_abaixo["abaixo" if acima else "acima"] += 1

    if not por_pagina:
        raise LayoutExtractionError("Nenhuma foto encontrada no capítulo do relatório fotográfico.")
    largura_pt, altura_pt = tamanhos.most_common(1)[0][0]
    fonte_legenda, tamanho_legenda = fontes_legenda.most_common(1)[0][0] if fontes_legenda else ("", 9.0)
    return {
        "fotos_por_pagina": max(por_pagina.items(), key=lambda item: (item[1], item[0]))[0],
        "colunas": colunas.most_common(1)[0][0],
        "foto_largura_cm": round(largura_pt * PONTO_EM_CM, 2),
        "foto_altura_cm": round(altura_pt * PONTO_EM_CM, 2),
        "legenda": {
            "rotulo": "Figura",
            "separador": separadores.most_common(1)[0][0] if separadores else "-",
            "fonte_padrao": anonimizar(fontes_citadas.most_common(1)[0][0]) if fontes_citadas else None,
            "familia": _familia_legivel(fonte_legenda) if fonte_legenda else None,
            "fonte_pt": tamanho_legenda,
            "italico": "italic" in fonte_legenda.lower() or "oblique" in fonte_legenda.lower(),
            "cor": cores_legenda.most_common(1)[0][0] if cores_legenda else "#000000",
            "posicao": legenda_abaixo.most_common(1)[0][0] if legenda_abaixo else "abaixo",
        },
    }


def _extrair_analise_por_sistema(pdf: pdfplumber.PDF, intervalo: range | None, corpo_pt: float) -> dict[str, Any]:
    """Subtítulos fixos que se repetem dentro de cada sistema ("➢ Constatações")."""
    if intervalo is None:
        return {"subtitulos": [], "marcador": None, "fonte_pt": corpo_pt}
    rotulos, marcadores, em_lista = Counter(), Counter(), Counter()
    for indice in intervalo:
        linhas = _linhas(pdf.pages[indice])
        for posicao, linha in enumerate(linhas):
            texto = linha["texto"].strip()
            # O marcador vem numa fonte de símbolos (Wingdings); o negrito é do rótulo.
            rotulo_negrito = all(_e_negrito(palavra["fontname"]) for palavra in linha["palavras"][1:])
            if not texto or texto[0] not in MARCADORES_SUBTITULO or not rotulo_negrito:
                continue
            # "Constatações:" e "Constatações" são o mesmo rótulo no original.
            rotulo = texto[1:].strip().rstrip(":").strip()
            if not rotulo or any(caractere.isdigit() for caractere in rotulo):
                continue
            rotulos[rotulo] += 1
            marcadores[texto[0]] += 1
            seguinte = linhas[posicao + 1]["texto"].strip() if posicao + 1 < len(linhas) else ""
            # Conteúdo em lista com marcador ("• Ralos com sujidades...") ou em parágrafos.
            if seguinte and seguinte[0] in "•▪-":
                em_lista[rotulo] += 1
    # Só é rótulo fixo o que se repete em mais de um sistema.
    fixos = [rotulo for rotulo, quantidade in rotulos.items() if quantidade >= 2]
    ordem = {rotulo: posicao for posicao, rotulo in enumerate(rotulos)}
    fixos.sort(key=lambda rotulo: ordem[rotulo])
    return {
        "subtitulos": [
            {
                "rotulo": anonimizar(rotulo),
                "chave": slug(rotulo),
                "lista": em_lista[rotulo] * 2 > rotulos[rotulo],
            }
            for rotulo in fixos
        ],
        "marcador": "➢" if marcadores else None,
        "fonte_pt": corpo_pt,
    }


def _extrair_assinatura(
    pdf: pdfplumber.PDF, paginas: list[tuple[int, Any]], secoes: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Bloco de assinatura: linha, imagem da rubrica, nome + qualificações e local/data."""
    for indice, pagina in paginas:
        linhas = _linhas(pagina)
        for posicao, linha in enumerate(linhas):
            if not RE_LINHA_ASSINATURA.match(linha["texto"].replace(" ", "")):
                continue
            abaixo = [item for item in linhas[posicao + 1 :] if item["top"] < float(pagina.height) * 0.9]
            bloco: list[dict[str, Any]] = []
            for item in abaixo:
                if RE_LOCAL_DATA.search(item["texto"]):
                    break
                if bloco and item["top"] - bloco[-1]["top"] > 3 * max(item["size"], 1):
                    break
                bloco.append(item)
            local_data = next((item for item in abaixo if RE_LOCAL_DATA.search(item["texto"])), None)
            rubrica = next(
                (
                    imagem
                    for imagem in _imagens_de_conteudo(pagina)
                    if float(imagem["top"]) < linha["top"] + 20 and float(imagem["bottom"]) > linha["top"] - 100
                ),
                None,
            )
            margem_direita = max(item["x1"] for item in [linha, *bloco])
            alinhados = sum(1 for item in bloco if abs(item["x1"] - margem_direita) < 5)
            secao = next(
                (secao["numero"] for secao in reversed(secoes) if secao["nivel"] == 1 and secao["_pagina"] <= indice),
                None,
            )
            return {
                "secao": secao,
                "alinhamento": "direita" if bloco and alinhados >= len(bloco) / 2 else "centro",
                "familia": _familia_legivel(bloco[0]["fontname"]) if bloco else _familia_legivel(linha["fontname"]),
                "fonte_pt": bloco[0]["size"] if bloco else linha["size"],
                "nome_negrito": bool(bloco and bloco[0]["negrito"]),
                "linhas_qualificacao_no_exemplar": max(len(bloco) - 1, 0),
                "rubrica": (
                    {
                        "largura_pt": round(float(rubrica["width"]), 1),
                        "altura_pt": round(float(rubrica["height"]), 1),
                    }
                    if rubrica
                    else None
                ),
                "local_data": local_data is not None,
            }
    return None


def _extrair_folha_de_rosto(pagina: Any, corpo_pt: float) -> dict[str, Any] | None:
    """Folha de rosto: bloco do título (fixo) separado da identificação do imóvel por um vão."""
    linhas = [linha for linha in _linhas(pagina) if linha["top"] < float(pagina.height) * 0.9]
    if not linhas:
        return None
    maior = max(linha["size"] for linha in linhas)
    if maior < corpo_pt * 2:
        return None
    grandes = [linha for linha in linhas if abs(linha["size"] - maior) < 0.5]
    vaos = [depois["top"] - antes["top"] for antes, depois in pairwise(grandes)]
    passo = sorted(vaos)[len(vaos) // 2] if vaos else 0
    blocos: list[list[dict[str, Any]]] = [[grandes[0]]]
    for vao, linha in zip(vaos, grandes[1:], strict=True):
        if passo and vao > passo * 1.6:
            blocos.append([])
        blocos[-1].append(linha)
    intermediarias = [linha for linha in linhas if corpo_pt < linha["size"] < maior - 0.5]
    return {
        "titulo": {
            "texto": anonimizar(" ".join(linha["texto"] for linha in blocos[0])),
            "linhas": [anonimizar(linha["texto"]) for linha in blocos[0]],
            "fonte_pt": maior,
            "familia": _familia_legivel(grandes[0]["fontname"]),
        },
        "identificacao": {"linhas_no_exemplar": sum(len(bloco) for bloco in blocos[1:]), "fonte_pt": maior},
        "data": {"fonte_pt": intermediarias[0]["size"]} if intermediarias else None,
    }


def _extrair_capa_vistoria(pagina: Any) -> dict[str, Any]:
    """Capa do LTIP (título + logo + fundo) acrescida do que a capa da vistoria tem a mais."""
    capa = _extrair_capa(pagina)
    capa["titulo"]["texto"] = anonimizar(capa["titulo"]["texto"])
    maior = capa["titulo"]["fonte_pt"]
    linhas = _linhas(pagina)
    capa["titulo"]["linhas"] = [anonimizar(linha["texto"]) for linha in linhas if abs(linha["size"] - maior) < 0.5]
    secundarias = sorted({linha["size"] for linha in linhas if linha["size"] < maior - 0.5}, reverse=True)
    rotulo = next(
        (RE_ROTULO_RESPONSAVEL.match(linha["texto"]).group(0) for linha in linhas if RE_ROTULO_RESPONSAVEL.match(linha["texto"])),
        None,
    )
    cores = Counter(_cor_do_caractere(caractere) for caractere in pagina.chars)
    capa["cor_texto"] = cores.most_common(1)[0][0] if cores else "#000000"
    capa["corpos_secundarios_pt"] = secundarias
    capa["rotulo_responsavel"] = rotulo
    if capa["logo"] is not None:
        centro = capa["logo"]["x_pt"] + capa["logo"]["largura_pt"] / 2
        capa["logo"]["alinhamento"] = "direita" if centro > float(pagina.width) * 0.6 else "centro"
    return capa


def extrair_layout(
    caminho_pdf: Path,
    *,
    tipo_documento: str = TIPO_DOCUMENTO,
    pagina_inicial_corpo: int = 4,
) -> dict[str, Any]:
    """Lê o PDF final da vistoria e devolve a especificação de layout, já sem dados pessoais.

    `pagina_inicial_corpo` (índice 0) pula capa, folha de rosto e sumário.
    """
    if not caminho_pdf.is_file():
        raise LayoutExtractionError(
            f"Original não encontrado em {caminho_pdf}. "
            "Os arquivos de 01_output-context/ ficam fora do Git — informe o caminho local."
        )

    with pdfplumber.open(caminho_pdf) as pdf:
        if len(pdf.pages) <= pagina_inicial_corpo:
            raise LayoutExtractionError(f"{caminho_pdf.name} tem menos páginas que capa + rosto + sumário.")

        primeira = pdf.pages[0]
        internas = [(indice, pagina) for indice, pagina in enumerate(pdf.pages) if indice >= pagina_inicial_corpo]
        internas_a4 = [(indice, pagina) for indice, pagina in internas if _e_a4(pagina)]
        de_texto = [pagina for _, pagina in internas_a4 if pagina.chars and not _imagens_de_conteudo(pagina)]
        if not de_texto:
            raise LayoutExtractionError(
                "Nenhuma página de texto corrido encontrada para medir o layout. "
                "Confira se o PDF informado é o laudo completo."
            )

        cabecalho = _extrair_cabecalho([pagina for _, pagina in internas_a4])
        provisorio = _extrair_tipografia_e_margens(de_texto, None)
        rodape = _extrair_rodape(de_texto, provisorio["cor_texto"], provisorio["tipografia"]["corpo_pt"])
        medidas = _extrair_tipografia_e_margens(de_texto, rodape["topo_pt"])
        tipografia = medidas["tipografia"]

        titulos = _extrair_hierarquia_de_titulos([pagina for _, pagina in internas_a4])
        tipografia["titulo_pt"] = max((titulo["fonte_pt"] for titulo in titulos), default=tipografia["corpo_pt"])

        secoes = _classificar_secoes(_extrair_secoes(internas_a4, tipografia["corpo_pt"]))
        if not secoes:
            raise LayoutExtractionError("Nenhum título numerado encontrado no corpo do laudo.")
        relatorio = _extrair_relatorio_fotografico(pdf, _intervalo_do_capitulo(secoes, "fotografico", len(pdf.pages)))
        tipografia["legenda_pt"] = relatorio["legenda"]["fonte_pt"]
        analise = _extrair_analise_por_sistema(
            pdf, _intervalo_do_capitulo(secoes, "por_sistema", len(pdf.pages)), tipografia["corpo_pt"]
        )
        assinatura = _extrair_assinatura(pdf, internas_a4, secoes)
        rosto = _extrair_folha_de_rosto(pdf.pages[1], tipografia["corpo_pt"]) if len(pdf.pages) > 1 else None

        largura_pt = round(float(primeira.width), 2)
        altura_pt = round(float(primeira.height), 2)
        e_a4 = _e_a4(primeira)
        layout = {
            "versao_schema": 1,
            "tipo_documento": tipo_documento,
            "origem": {
                # O nome do arquivo identifica a unidade vistoriada ("... - Ap. NNNN.pdf"):
                # só o hash vai para o artefato versionado.
                "sha256": _sha256(caminho_pdf),
                "paginas": len(pdf.pages),
                "paginas_fora_do_a4": len(pdf.pages) - sum(1 for pagina in pdf.pages if _e_a4(pagina)),
            },
            "pagina": {
                "tamanho": "A4" if e_a4 else f"{largura_pt}x{altura_pt}pt",
                "orientacao": "portrait" if altura_pt >= largura_pt else "landscape",
                "largura_pt": largura_pt,
                "altura_pt": altura_pt,
                "margens_cm": medidas["margens_cm"],
            },
            "tipografia": tipografia,
            "titulos": titulos,
            "cores": {
                "texto": medidas["cor_texto"],
                "legenda": relatorio["legenda"]["cor"],
                "link": rodape["cor_link"],
                "capa_texto": None,
            },
            "capa": _extrair_capa_vistoria(primeira),
            "folha_de_rosto": rosto,
            "cabecalho": cabecalho,
            "rodape": rodape,
            "secoes": [
                {
                    "numero": secao["numero"],
                    "nivel": secao["nivel"],
                    "titulo": anonimizar(secao["titulo"]),
                    "tipo": secao["tipo"],
                }
                for secao in secoes
            ],
            "relatorio_fotografico": relatorio,
            "analise_por_sistema": analise,
            "assinatura": assinatura,
        }
        layout["cores"]["capa_texto"] = layout["capa"]["cor_texto"]

    verificar_sem_dados_pessoais(layout)
    return layout
