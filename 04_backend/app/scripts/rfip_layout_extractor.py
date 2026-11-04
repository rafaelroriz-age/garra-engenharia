"""Extração determinística do layout do RFIP a partir da planilha original do cliente.

Implementa a primeira metade de ADR-13/DEC-25 (`00_docs/arquitetura.md`) para o
Relatório Fotográfico de Inspeção Predial: lê o `.xlsx` original e produz
`templates/rfip/layout.json`, do qual derivam o `.html.j2` (WeasyPrint) e o
`.docx` (docxtpl) — PDF e DOCX saem da mesma especificação.

O original tem ~479 MB, quase todos de fotos em `xl/media/`. Por isso:

* as células são lidas com ``openpyxl.load_workbook(read_only=True)`` (streaming)
  e só as primeiras ``max_linhas`` linhas da aba fotográfica são percorridas;
* o que o modo read_only do openpyxl não expõe (larguras e colunas ocultas,
  alturas de linha, mesclagens, margens, cabeçalho/rodapé, quebras de página,
  âncoras das fotos) vem de um ``iterparse`` do XML da aba, também em streaming;
* nenhuma imagem é extraída: das fotos lê-se só a âncora em
  `xl/drawings/drawingN.xml` (posição e tamanho), nunca `xl/media/*`.

DEC-35: o `layout.json` guarda só geometria e rótulos fixos. Valores preenchidos
no exemplar (situação, notas GUT, observações, localização, títulos de sistema)
e a identificação do responsável no rodapé (nome, CREA, e-mail, telefone) viram
papéis/placeholders. O nome do arquivo original identifica a obra e não entra no
JSON; a procedência é o sha256. Um verificador fail-closed recusa o layout se
sobrar dado pessoal (OWASP A02).
"""

from __future__ import annotations

import hashlib
import posixpath
import re
import unicodedata
import warnings
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from itertools import pairwise
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter

TIPO_DOCUMENTO = "RFIP"
POLEGADA_EM_CM = 2.54
EMU_POR_CM = 360_000
PONTOS_POR_POLEGADA = 72
#: `pageSetup/@paperSize` do OOXML — 9 é A4 (21 x 29,7 cm).
PAPER_SIZE_A4 = 9
PAPEL_CM = {PAPER_SIZE_A4: (21.0, 29.7)}
#: Convenção do Excel para converter largura de coluna (em caracteres) em pixels:
#: px = trunc(((256·w + trunc(128/mdw)) / 256) · mdw), com mdw = largura máxima de
#: um dígito da fonte padrão em px a 96 dpi. 7 px é o valor do Excel para as fontes
#: padrão de 10-11 pt; é uma convenção de conversão, não uma medida do original.
LARGURA_DIGITO_PX = 7
DPI_TELA = 96
#: Teto de tamanho descompactado para qualquer XML lido do pacote (zip bomb, A05).
LIMITE_XML_BYTES = 64 * 1024 * 1024
#: Linhas lidas da aba fotográfica: cobre 4 fichas, 1 título de sistema e 2 quebras de página.
MAX_LINHAS_PADRAO = 120
MAX_COLUNAS = 26

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
NS_XDR = "{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}"
NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

RE_FOTO = re.compile(r"^\s*(foto\s*n?[º°o.]*)\s*(\d+)\s*$", re.IGNORECASE)
RE_TITULO_NUMERADO = re.compile(r"^\s*(\d+)\.(\d+)(?:\.\d+)*\.?\s+\S")
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
RE_TELEFONE = re.compile(r"\(?\b\d{2}\)?\s*9?\s*\d{4}-?\d{4}\b")
RE_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
RE_CNPJ = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
RE_CEP = re.compile(r"\b\d{5}-\d{3}\b")
RE_NUMERO_LONGO = re.compile(r"\d{6,}")
RE_CREA = re.compile(r"\bCREA\b", re.IGNORECASE)
RE_COR_HEX = re.compile(r"#[0-9A-F]{6}")
#: Escape `_xHHHH_` do OOXML (ST_Xstring) — p.ex. `_x000a_` é a quebra de linha do rodapé.
RE_ESCAPE_OOXML = re.compile(r"_x([0-9A-Fa-f]{4})_")
RE_VML_DIMENSAO = re.compile(r"(width|height)\s*:\s*([\d.]+)pt", re.IGNORECASE)
RE_VML_SHAPE = re.compile(r"<v:shape\b[^>]*\bid=\"(?P<id>[LCR][HF])\"[^>]*style='(?P<style>[^']*)'", re.IGNORECASE | re.DOTALL)

PH_NOME = "{{ responsavel.nome }}"
PH_REGISTRO = "{{ responsavel.titulo_profissional }} - CREA nº {{ responsavel.crea }}"
PH_EMAIL = "{{ responsavel.email }}"
PH_TELEFONE = "{{ responsavel.telefone }}"
PH_PAGINA = "{{ numero_pagina }}"

#: Ordem do esquema de cores do tema no índice do Excel (0 = lt1, 1 = dk1, ...).
ORDEM_CORES_TEMA = ("lt1", "dk1", "lt2", "dk2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink")


class LayoutExtractionError(RuntimeError):
    """Erro irrecuperável ao ler o original — nunca degrada para valor inventado."""


# --------------------------------------------------------------------------- util


def slug(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", sem_acento.casefold()).strip("_")


def _texto(valor: Any) -> str:
    return " ".join(str(valor).split()) if valor is not None else ""


def _moda(valores: list[Any], padrao: Any = None) -> Any:
    return Counter(valores).most_common(1)[0][0] if valores else padrao


def _cm(valor: float) -> float:
    return round(valor, 2)


def _desescapar(texto: str | None) -> str:
    return RE_ESCAPE_OOXML.sub(lambda achado: chr(int(achado.group(1), 16)), texto or "")


def _sha256(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _abrir_xml(pacote: zipfile.ZipFile, membro: str):
    info = pacote.getinfo(membro)
    if info.file_size > LIMITE_XML_BYTES:
        raise LayoutExtractionError(f"{membro} descompactado tem {info.file_size} bytes, acima do limite de leitura.")
    return pacote.open(info)


def _ler_xml(pacote: zipfile.ZipFile, membro: str) -> ET.Element:
    with _abrir_xml(pacote, membro) as arquivo:
        return ET.parse(arquivo).getroot()


def _rels(pacote: zipfile.ZipFile, membro: str) -> dict[str, str]:
    """Relações de uma parte OOXML: id -> caminho absoluto dentro do pacote."""
    pasta, nome = posixpath.split(membro)
    caminho_rels = posixpath.join(pasta, "_rels", nome + ".rels")
    if caminho_rels not in pacote.namelist():
        return {}
    relacoes: dict[str, str] = {}
    for rel in _ler_xml(pacote, caminho_rels).iter(f"{NS_PKG_REL}Relationship"):
        alvo = rel.get("Target", "")
        relacoes[rel.get("Id", "")] = alvo.lstrip("/") if alvo.startswith("/") else posixpath.normpath(posixpath.join(pasta, alvo))
    return relacoes


def _partes_das_abas(pacote: zipfile.ZipFile) -> dict[str, str]:
    """Nome da aba -> caminho do XML (`xl/worksheets/sheetN.xml`)."""
    relacoes = _rels(pacote, "xl/workbook.xml")
    abas: dict[str, str] = {}
    for aba in _ler_xml(pacote, "xl/workbook.xml").iter(f"{NS_MAIN}sheet"):
        abas[aba.get("name", "")] = relacoes.get(aba.get(f"{NS_REL}id", ""), "")
    return abas


def _cores_do_tema(pacote: zipfile.ZipFile) -> list[str | None]:
    if "xl/theme/theme1.xml" not in pacote.namelist():
        return [None] * len(ORDEM_CORES_TEMA)
    raiz = _ler_xml(pacote, "xl/theme/theme1.xml")
    esquema = next(raiz.iter(f"{NS_A}clrScheme"), None)
    cores: dict[str, str] = {}
    if esquema is not None:
        for filho in esquema:
            nome = filho.tag.replace(NS_A, "")
            rgb = next(filho.iter(f"{NS_A}srgbClr"), None)
            sistema = next(filho.iter(f"{NS_A}sysClr"), None)
            valor = rgb.get("val") if rgb is not None else (sistema.get("lastClr") if sistema is not None else None)
            if valor:
                cores[nome] = f"#{valor.upper()}"
    # No índice do Excel, 0/1 apontam para lt1/dk1 (ordem invertida em relação ao XML).
    return [cores.get(nome) for nome in ORDEM_CORES_TEMA]


def _fonte_padrao(pacote: zipfile.ZipFile) -> dict[str, Any]:
    """Primeira `<font>` de `styles.xml`: fonte do estilo Normal, usada pelo `&"-,..."` do rodapé."""
    raiz = _ler_xml(pacote, "xl/styles.xml")
    fontes = raiz.find(f"{NS_MAIN}fonts")
    fonte = fontes.find(f"{NS_MAIN}font") if fontes is not None else None
    if fonte is None:
        raise LayoutExtractionError("styles.xml não declara nenhuma fonte.")
    nome = fonte.find(f"{NS_MAIN}name")
    tamanho = fonte.find(f"{NS_MAIN}sz")
    return {
        "familia": nome.get("val") if nome is not None else None,
        "corpo_pt": float(tamanho.get("val")) if tamanho is not None else None,
    }


def _aplicar_tint(cor: str, tint: float | None) -> str:
    if not tint:
        return cor
    canais = [int(cor[i : i + 2], 16) for i in (1, 3, 5)]
    if tint < 0:
        canais = [round(c * (1 + tint)) for c in canais]
    else:
        canais = [round(c + (255 - c) * tint) for c in canais]
    return "#" + "".join(f"{max(0, min(255, c)):02X}" for c in canais)


def _resolver_cor(cor: Any, tema: list[str | None]) -> str | None:
    if cor is None:
        return None
    if getattr(cor, "type", None) == "rgb" and isinstance(cor.rgb, str) and len(cor.rgb) == 8:
        return f"#{cor.rgb[2:].upper()}"
    if getattr(cor, "type", None) == "theme" and isinstance(cor.theme, int) and cor.theme < len(tema):
        base = tema[cor.theme]
        return _aplicar_tint(base, cor.tint) if base else None
    return None


# ------------------------------------------------------- leitura de células (openpyxl)


def _estilo(celula: Any, tema: list[str | None]) -> dict[str, Any]:
    fonte = celula.font
    preenchimento = celula.fill
    fundo = None
    if preenchimento is not None and preenchimento.fill_type == "solid":
        fundo = _resolver_cor(preenchimento.fgColor, tema)
    bordas = {
        lado: getattr(getattr(celula.border, lado, None), "style", None)
        for lado in ("left", "right", "top", "bottom")
    }
    return {
        "fonte": fonte.name if fonte is not None else None,
        "corpo_pt": float(fonte.sz) if fonte is not None and fonte.sz else None,
        "negrito": bool(fonte is not None and fonte.b),
        "italico": bool(fonte is not None and fonte.i),
        "cor": _resolver_cor(fonte.color, tema) if fonte is not None else None,
        "fundo": fundo,
        "alinhamento_h": celula.alignment.horizontal if celula.alignment is not None else None,
        "alinhamento_v": celula.alignment.vertical if celula.alignment is not None else None,
        "quebra_texto": bool(celula.alignment is not None and celula.alignment.wrap_text),
        "bordas": {lado: estilo for lado, estilo in bordas.items() if estilo},
    }


def _ler_celulas(ws: Any, max_linhas: int, tema: list[str | None]) -> dict[tuple[int, int], dict[str, Any]]:
    """Células com conteúdo ou estilo visível nas primeiras `max_linhas` linhas.

    O texto fica só em memória, para classificar rótulo x valor; o que é gravado
    no layout.json é decidido depois, em `_montar_ficha`.
    """
    celulas: dict[tuple[int, int], dict[str, Any]] = {}
    for linha in ws.iter_rows(min_row=1, max_row=max_linhas, max_col=MAX_COLUNAS):
        for celula in linha:
            if not hasattr(celula, "font") or getattr(celula, "row", None) is None:
                continue  # EmptyCell do modo read_only: sem valor nem estilo
            estilo = _estilo(celula, tema)
            texto = _texto(celula.value)
            if not texto and not estilo["fundo"] and not estilo["bordas"]:
                continue
            celulas[(celula.row, celula.column)] = {"texto": texto, **estilo}
    return celulas


# ------------------------------------------------- leitura do XML da aba (streaming)


def _ler_metadados_da_aba(pacote: zipfile.ZipFile, membro: str, max_linhas: int) -> dict[str, Any]:
    """Colunas, alturas, mesclagens, página e cabeçalho/rodapé num único passe."""
    colunas: dict[int, dict[str, Any]] = {}
    alturas: dict[int, float] = {}
    mesclagens: list[str] = []
    quebras: list[int] = []
    resultado: dict[str, Any] = {"margens": {}, "pagina": {}, "cabecalho": None, "rodape": None, "ajustar": {}}
    altura_padrao = None
    em_quebras_de_linha = False
    with _abrir_xml(pacote, membro) as arquivo:
        for evento, elemento in ET.iterparse(arquivo, events=("start", "end")):
            tag = elemento.tag.replace(NS_MAIN, "")
            if tag == "rowBreaks":
                em_quebras_de_linha = evento == "start"
                continue
            if evento == "start":
                continue
            if tag == "row":
                numero = int(elemento.get("r", "0"))
                if numero <= max_linhas and elemento.get("ht"):
                    alturas[numero] = float(elemento.get("ht"))
                elemento.clear()
            elif tag == "col":
                for indice in range(int(elemento.get("min")), int(elemento.get("max")) + 1):
                    if indice > MAX_COLUNAS:
                        break
                    colunas[indice] = {
                        "largura": float(elemento.get("width", "0")),
                        "oculta": elemento.get("hidden") in ("1", "true"),
                    }
            elif tag == "sheetFormatPr":
                altura_padrao = float(elemento.get("defaultRowHeight", "15"))
                resultado["largura_padrao"] = float(elemento.get("defaultColWidth", "8.43"))
            elif tag == "sheetPr":
                ajuste = elemento.find(f"{NS_MAIN}pageSetUpPr")
                resultado["ajustar"]["ativo"] = ajuste is not None and ajuste.get("fitToPage") in ("1", "true")
            elif tag == "mergeCell":
                ref = elemento.get("ref", "")
                inicio = re.match(r"[A-Z]+(\d+)", ref)
                if inicio and int(inicio.group(1)) <= max_linhas:
                    mesclagens.append(ref)
                elemento.clear()
            elif tag == "pageMargins":
                resultado["margens"] = {chave: float(valor) for chave, valor in elemento.attrib.items()}
            elif tag == "pageSetup":
                resultado["pagina"] = dict(elemento.attrib)
            elif tag == "oddHeader":
                resultado["cabecalho"] = _desescapar(elemento.text)
            elif tag == "oddFooter":
                resultado["rodape"] = _desescapar(elemento.text)
            elif tag == "brk" and em_quebras_de_linha and elemento.get("id"):
                quebras.append(int(elemento.get("id")))
            elif tag == "drawing":
                resultado["drawing_rid"] = elemento.get(f"{NS_REL}id")
            elif tag == "legacyDrawingHF":
                resultado["vml_rid"] = elemento.get(f"{NS_REL}id")
    resultado.update(
        colunas=colunas,
        alturas=alturas,
        altura_padrao=altura_padrao or 15.0,
        mesclagens=mesclagens,
        quebras=sorted(quebras),
    )
    return resultado


def _ancoras_das_fotos(pacote: zipfile.ZipFile, membro: str | None, max_linhas: int) -> list[dict[str, Any]]:
    """Posição e tamanho das fotos ancoradas — só o XML do desenho, nunca `xl/media`."""
    if not membro or membro not in pacote.namelist():
        return []
    ancoras: list[dict[str, Any]] = []
    with _abrir_xml(pacote, membro) as arquivo:
        for _evento, elemento in ET.iterparse(arquivo, events=("end",)):
            if elemento.tag not in (f"{NS_XDR}twoCellAnchor", f"{NS_XDR}oneCellAnchor"):
                continue
            if elemento.find(f"{NS_XDR}pic") is None:
                elemento.clear()
                continue
            origem = elemento.find(f"{NS_XDR}from")
            linha = int(origem.findtext(f"{NS_XDR}row", "0"))
            if linha < max_linhas:
                extensao = elemento.find(f".//{NS_A}xfrm/{NS_A}ext")
                if extensao is None:
                    extensao = elemento.find(f"{NS_XDR}ext")
                ancoras.append(
                    {
                        "linha": linha + 1,
                        "coluna": int(origem.findtext(f"{NS_XDR}col", "0")) + 1,
                        "deslocamento_x_cm": _cm(int(origem.findtext(f"{NS_XDR}colOff", "0")) / EMU_POR_CM),
                        "deslocamento_y_cm": _cm(int(origem.findtext(f"{NS_XDR}rowOff", "0")) / EMU_POR_CM),
                        "largura_cm": _cm(int(extensao.get("cx", "0")) / EMU_POR_CM) if extensao is not None else None,
                        "altura_cm": _cm(int(extensao.get("cy", "0")) / EMU_POR_CM) if extensao is not None else None,
                    }
                )
            elemento.clear()
    return ancoras


def _imagens_de_cabecalho(pacote: zipfile.ZipFile, membro: str | None) -> dict[str, dict[str, float]]:
    """Tamanho das imagens de cabeçalho/rodapé (`&G`) declaradas no VML (LH/CH/RH/LF/...)."""
    if not membro or membro not in pacote.namelist():
        return {}
    with _abrir_xml(pacote, membro) as arquivo:
        vml = arquivo.read().decode("utf-8", errors="replace")
    imagens: dict[str, dict[str, float]] = {}
    for achado in RE_VML_SHAPE.finditer(vml):
        dimensoes = {chave.lower(): float(valor) for chave, valor in RE_VML_DIMENSAO.findall(achado.group("style"))}
        if "width" in dimensoes and "height" in dimensoes:
            imagens[achado.group("id").upper()] = {
                "largura_cm": _cm(dimensoes["width"] / PONTOS_POR_POLEGADA * POLEGADA_EM_CM),
                "altura_cm": _cm(dimensoes["height"] / PONTOS_POR_POLEGADA * POLEGADA_EM_CM),
            }
    return imagens


# ----------------------------------------------------- cabeçalho e rodapé do Excel


def _cor_do_codigo(codigo: str, tema: list[str | None]) -> str | None:
    """`&K` do Excel: `RRGGBB` ou `TTSNNN` (tema, sinal e tint em milésimos)."""
    if re.fullmatch(r"[0-9A-Fa-f]{6}", codigo):
        return f"#{codigo.upper()}"
    achado = re.fullmatch(r"(\d{2})([+-])(\d{3})", codigo)
    if achado and int(achado.group(1)) < len(tema) and tema[int(achado.group(1))]:
        tint = int(achado.group(3)) / 100 * (-1 if achado.group(2) == "-" else 1)
        return _aplicar_tint(tema[int(achado.group(1))], tint)
    return None


def _segmentar_cabecalho_rodape(codigo: str, tema: list[str | None]) -> dict[str, list[list[dict[str, Any]]]]:
    """Divide o código `&L/&C/&R` em seções -> linhas -> trechos com estilo."""
    secoes: dict[str, list[list[dict[str, Any]]]] = {}
    secao = "C"
    negrito = False
    cor: str | None = None
    texto = ""

    def emitir(campo: str | None = None) -> None:
        nonlocal texto
        linhas = secoes.setdefault(secao, [[]])
        if texto:
            partes = texto.split("\n")
            for indice, parte in enumerate(partes):
                if indice:
                    linhas.append([])
                if parte:
                    linhas[-1].append({"texto": parte, "negrito": negrito, "cor": cor})
            texto = ""
        if campo:
            linhas[-1].append({"campo": campo, "negrito": negrito, "cor": cor})

    posicao = 0
    while posicao < len(codigo):
        caractere = codigo[posicao]
        if caractere != "&" or posicao + 1 >= len(codigo):
            texto += caractere
            posicao += 1
            continue
        seguinte = codigo[posicao + 1]
        if seguinte == "&":
            texto += "&"
            posicao += 2
        elif seguinte in "LCR":
            emitir()
            secao = seguinte
            posicao += 2
        elif seguinte == '"':
            fim = codigo.index('"', posicao + 2)
            emitir()
            estilo = codigo[posicao + 2 : fim].split(",")[-1].casefold()
            negrito = any(chave in estilo for chave in ("bold", "negrito"))
            posicao = fim + 1
        elif seguinte == "K":
            emitir()
            cor = _cor_do_codigo(codigo[posicao + 2 : posicao + 8], tema)
            posicao += 8
        elif seguinte == "B":
            emitir()
            negrito = not negrito
            posicao += 2
        elif seguinte in "PNG":
            emitir({"P": "numero_pagina", "N": "total_paginas", "G": "imagem"}[seguinte])
            posicao += 2
        else:
            # &D, &T, &F, &A, &nn (corpo) etc.: códigos sem efeito no layout medido.
            emitir()
            posicao += 2
            while posicao < len(codigo) and codigo[posicao].isdigit():
                posicao += 1
    emitir()
    return {chave: [linha for linha in linhas if linha] for chave, linhas in secoes.items() if any(linhas)}


def _modelar_trecho(trecho: dict[str, Any], linha_texto: str, primeira_linha: bool) -> dict[str, Any] | None:
    """Troca o texto do exemplar pelo papel que ele cumpre — o texto nunca é guardado."""
    estilo = {"negrito": trecho["negrito"], "cor": trecho["cor"]}
    if "campo" in trecho:
        placeholder = {"numero_pagina": PH_PAGINA, "total_paginas": "{{ total_paginas }}", "imagem": None}[trecho["campo"]]
        return {"papel": trecho["campo"], "placeholder": placeholder, **estilo}
    texto = trecho["texto"]
    # CREA antes de telefone: o nº de registro (10 dígitos) também casa RE_TELEFONE.
    if RE_CREA.search(linha_texto):
        return {"papel": "registro", "placeholder": PH_REGISTRO, **estilo}
    partes: list[str] = []
    resto = texto
    for detector, placeholder in ((RE_EMAIL, PH_EMAIL), (RE_TELEFONE, PH_TELEFONE)):
        if detector.search(resto):
            partes.append(placeholder)
            resto = detector.sub("", resto)
    if partes:
        separador = " / " if "/" in resto else " "
        prefixo = separador if texto[:1].isspace() or texto.lstrip().startswith("/") else ""
        return {"papel": "contato", "placeholder": prefixo + separador.join(partes), **estilo}
    if primeira_linha and texto.strip():
        return {"papel": "nome", "placeholder": PH_NOME, **estilo}
    return None  # texto livre não reconhecido: descartado (fail-closed)


def _modelar_cabecalho_rodape(codigo: str | None, tema: list[str | None], imagens: dict[str, dict[str, float]], sufixo: str) -> dict[str, Any]:
    if not codigo:
        return {"secoes": {}}
    secoes_modeladas: dict[str, Any] = {}
    for secao, linhas in _segmentar_cabecalho_rodape(codigo, tema).items():
        linhas_modeladas = []
        for indice, linha in enumerate(linhas):
            linha_texto = "".join(trecho.get("texto", "") for trecho in linha)
            trechos = [_modelar_trecho(trecho, linha_texto, indice == 0) for trecho in linha]
            trechos = [trecho for trecho in trechos if trecho is not None]
            if not trechos:
                continue
            papeis = {trecho["papel"] for trecho in trechos}
            papel = "contato" if "contato" in papeis else trechos[0]["papel"]
            linha_modelada: dict[str, Any] = {"papel": papel, "trechos": trechos}
            if "imagem" in papeis:
                linha_modelada["imagem"] = imagens.get(secao + sufixo)
            linhas_modeladas.append(linha_modelada)
        if linhas_modeladas:
            secoes_modeladas[{"L": "esquerda", "C": "centro", "R": "direita"}[secao]] = linhas_modeladas
    return {"secoes": secoes_modeladas}


# ------------------------------------------------------------- geometria da ficha


def _largura_px(largura_chars: float) -> int:
    return int(((256 * largura_chars + int(128 / LARGURA_DIGITO_PX)) / 256) * LARGURA_DIGITO_PX)


def _intervalo(ref: str) -> tuple[int, int, int, int]:
    inicio, _, fim = ref.partition(":")
    fim = fim or inicio
    a = re.match(r"([A-Z]+)(\d+)", inicio)
    b = re.match(r"([A-Z]+)(\d+)", fim)
    return (int(a.group(2)), column_index_from_string(a.group(1)), int(b.group(2)), column_index_from_string(b.group(1)))


def _pagina(meta: dict[str, Any]) -> dict[str, Any]:
    pagina = meta["pagina"]
    margens = meta["margens"]
    if not margens:
        raise LayoutExtractionError("A aba fotográfica não declara margens de página (<pageMargins>).")
    tamanho_codigo = int(pagina.get("paperSize", PAPER_SIZE_A4))
    return {
        "tamanho": "A4" if tamanho_codigo == PAPER_SIZE_A4 else str(tamanho_codigo),
        "orientacao": pagina.get("orientation", "portrait"),
        "margens_cm": {
            "esquerda": _cm(margens.get("left", 0) * POLEGADA_EM_CM),
            "direita": _cm(margens.get("right", 0) * POLEGADA_EM_CM),
            "superior": _cm(margens.get("top", 0) * POLEGADA_EM_CM),
            "inferior": _cm(margens.get("bottom", 0) * POLEGADA_EM_CM),
            "cabecalho": _cm(margens.get("header", 0) * POLEGADA_EM_CM),
            "rodape": _cm(margens.get("footer", 0) * POLEGADA_EM_CM),
        },
        "ajustar_largura_a_pagina": bool(meta["ajustar"].get("ativo")) and pagina.get("fitToWidth", "1") == "1",
        # Posição do RFIP dentro do laudo no exemplar (anexo numerado em sequência), não do modelo.
        "primeira_pagina_no_original": (
            int(pagina["firstPageNumber"]) if pagina.get("useFirstPageNumber") in ("1", "true") and pagina.get("firstPageNumber") else None
        ),
    }


def _celula_coberta(mesclagens: list[tuple[int, int, int, int]], linha: int, coluna: int) -> tuple[int, int, int, int] | None:
    for intervalo in mesclagens:
        if intervalo[0] <= linha <= intervalo[2] and intervalo[1] <= coluna <= intervalo[3]:
            return intervalo
    return None


def _marcadores_de_campo(celulas: dict[tuple[int, int], dict[str, Any]], colunas_ocultas: set[int], linha_foto: int, periodo: int, numero: str) -> dict[str, int]:
    """Coluna auxiliar oculta: `<CAMPO> Foto nº NN` marca a linha do valor de cada campo.

    É a chave que a aba de resumo usa no PROCV — portanto o dicionário de dados do
    próprio original, e não uma inferência sobre o texto preenchido.
    """
    marcadores: dict[str, int] = {}
    sufixo = re.compile(rf"\s+foto\s*n?[º°o.]*\s*0*{int(numero)}\s*$", re.IGNORECASE)
    for (linha, coluna), celula in celulas.items():
        if coluna not in colunas_ocultas or not (linha_foto <= linha < linha_foto + periodo):
            continue
        achado = sufixo.search(celula["texto"])
        if achado:
            marcadores[celula["texto"][: achado.start()].strip()] = linha - linha_foto
    return marcadores


def _fichas_no_trecho(celulas: dict[tuple[int, int], dict[str, Any]], colunas_ocultas: set[int]) -> list[tuple[int, int, str, str]]:
    fichas = []
    for (linha, coluna), celula in sorted(celulas.items()):
        if coluna in colunas_ocultas:
            continue
        achado = RE_FOTO.match(celula["texto"])
        if achado:
            fichas.append((linha, coluna, achado.group(1).strip(), achado.group(2)))
    return fichas


def _estilo_persistido(celula: dict[str, Any]) -> dict[str, Any]:
    return {chave: valor for chave, valor in celula.items() if chave != "texto"}


def _montar_ficha(
    celulas: dict[tuple[int, int], dict[str, Any]],
    meta: dict[str, Any],
    ancoras: list[dict[str, Any]],
    colunas_impressas: list[int],
    max_linhas: int,
) -> dict[str, Any]:
    colunas_ocultas = {indice for indice, coluna in meta["colunas"].items() if coluna["oculta"]}
    fichas = _fichas_no_trecho(celulas, colunas_ocultas)
    if not fichas:
        raise LayoutExtractionError("Nenhuma legenda 'Foto nº NN' encontrada nas primeiras linhas da aba fotográfica.")
    linhas_fichas = [linha for linha, _, _, _ in fichas]
    diferencas = [b - a for a, b in pairwise(linhas_fichas) if b > a]
    if not diferencas:
        raise LayoutExtractionError("É preciso ao menos duas fichas nas linhas lidas para medir a altura da ficha.")
    # Fichas consecutivas (sem título de sistema entre elas) distam exatamente uma ficha.
    periodo = min(diferencas)
    linha0, _coluna, prefixo_legenda, numero = fichas[0]
    # Só fichas inteiras dentro das linhas lidas servem de amostra para "rótulo fixo".
    amostras = [linha for linha in linhas_fichas if linha + periodo - 1 <= max_linhas]

    mesclagens = [_intervalo(ref) for ref in meta["mesclagens"]]
    marcadores = _marcadores_de_campo(celulas, colunas_ocultas, linha0, periodo, numero)
    if not marcadores:
        raise LayoutExtractionError("A ficha não tem a coluna auxiliar '<CAMPO> Foto nº NN' que localiza os valores.")
    ancoras_ficha = [a for a in ancoras if linha0 <= a["linha"] < linha0 + periodo]

    def texto_em(base: int, deslocamento: int, coluna: int) -> str:
        return celulas.get((base + deslocamento, coluna), {}).get("texto", "")

    # Célula de valor de cada campo: linha do marcador, coluna do rótulo — ou, quando
    # rótulo e valor dividem a linha (notas GUT), a próxima coluna visível.
    valores: dict[tuple[int, int], str] = {}
    for rotulo, deslocamento in marcadores.items():
        alvo = slug(rotulo)
        candidatos = sorted(
            (linha - linha0, coluna)
            for (linha, coluna), celula in celulas.items()
            if linha0 <= linha < linha0 + periodo and coluna not in colunas_ocultas and slug(celula["texto"]) == alvo
        )
        if not candidatos:
            continue
        rotulo_linha, rotulo_coluna = candidatos[0]
        if rotulo_linha == deslocamento:
            mescla = _celula_coberta(mesclagens, linha0 + rotulo_linha, rotulo_coluna)
            proxima = (mescla[3] if mescla else rotulo_coluna) + 1
            while proxima in colunas_ocultas:
                proxima += 1
            valores[(deslocamento, proxima)] = alvo
        else:
            valores[(deslocamento, rotulo_coluna)] = alvo
    campos_tipo = {slug(rotulo) for rotulo in marcadores if slug(rotulo).startswith("tipo_de_")}

    celulas_ficha: list[dict[str, Any]] = []
    vistos: set[tuple[int, int]] = set()
    for deslocamento in range(periodo):
        linha = linha0 + deslocamento
        for coluna in colunas_impressas:
            if (linha, coluna) in vistos:
                continue
            mescla = _celula_coberta(mesclagens, linha, coluna)
            linhas_span = list(range(linha, (mescla[2] if mescla else linha) + 1))
            inicio, fim = (mescla[1], mescla[3]) if mescla else (coluna, coluna)
            colunas_span = [c for c in colunas_impressas if inicio <= c <= fim]
            vistos.update((lin, col) for lin in linhas_span for col in colunas_span)
            celula = celulas.get((mescla[0], mescla[1]) if mescla else (linha, coluna)) or celulas.get((linha, coluna))
            foto = any(
                linhas_span[0] <= a["linha"] <= linhas_span[-1] and colunas_span[0] <= a["coluna"] <= colunas_span[-1]
                for a in ancoras_ficha
            )
            if celula is None and not foto:
                continue
            registro: dict[str, Any] = {
                "linha": deslocamento,
                "coluna": get_column_letter(coluna),
                "linhas": len(linhas_span),
                "colunas": len(colunas_span),
            }
            texto = celula["texto"] if celula else ""
            if RE_FOTO.match(texto):
                registro.update(papel="titulo_foto")
            elif foto and not texto:
                registro["papel"] = "foto"
            elif (deslocamento, coluna) in valores:
                registro.update(papel="valor", campo=valores[(deslocamento, coluna)])
            elif texto.casefold().startswith("tipo de ") and slug(texto) in campos_tipo:
                # "TIPO DE ANOMALIA"/"TIPO DE FALHA": o sufixo acompanha a classificação
                # da ficha (a aba de resumo monta a chave com "TIPO DE "&Classificação).
                registro.update(papel="rotulo", texto=texto[: len("tipo de")].upper(), sufixo_campo="classificacao")
            elif texto and len(amostras) >= 2 and all(texto_em(base, deslocamento, coluna) == texto for base in amostras):
                registro.update(papel="rotulo", texto=texto)
            elif texto:
                registro["papel"] = "descartado"  # texto do exemplar: só a geometria fica
            else:
                registro["papel"] = "vazio"
            if celula:
                estilo = _estilo_persistido(celula)
                if mescla:
                    # Bordas direita/inferior de uma mesclagem moram nas células da borda.
                    bordas = dict(estilo["bordas"])
                    for lado, membros in (
                        ("right", [(lin, colunas_span[-1]) for lin in linhas_span]),
                        ("bottom", [(linhas_span[-1], c) for c in colunas_span]),
                    ):
                        achado = next((celulas[m]["bordas"][lado] for m in membros if lado in celulas.get(m, {}).get("bordas", {})), None)
                        if achado:
                            bordas[lado] = achado
                    estilo["bordas"] = bordas
                registro["estilo"] = estilo
            celulas_ficha.append(registro)

    # Fichas por página: legendas "Foto nº" entre duas quebras manuais consecutivas.
    quebras = [0, *[q for q in meta["quebras"] if q <= max_linhas]]
    contagem = [sum(1 for linha in linhas_fichas if a < linha <= b) for a, b in pairwise(quebras)]

    foto = None
    if ancoras:
        larguras = sorted(a["largura_cm"] for a in ancoras if a["largura_cm"])
        alturas = sorted(a["altura_cm"] for a in ancoras if a["altura_cm"])
        foto = {
            "largura_cm": larguras[len(larguras) // 2] if larguras else None,
            "altura_cm": alturas[len(alturas) // 2] if alturas else None,
            "amostras": len(ancoras),
        }

    return {
        "linhas_por_ficha": periodo,
        "fichas_por_pagina": _moda([c for c in contagem if c], None),
        "fichas_amostradas": len(amostras),
        "alturas_pt": [meta["alturas"].get(linha0 + d, meta["altura_padrao"]) for d in range(periodo)],
        "legenda": {"prefixo": prefixo_legenda, "digitos": len(numero)},
        "campos": [
            {"campo": slug(rotulo), "rotulo": rotulo, "linha_valor": deslocamento}
            for rotulo, deslocamento in sorted(marcadores.items(), key=lambda item: item[1])
        ],
        "foto": foto,
        "celulas": celulas_ficha,
        "_linha_inicial": linha0,
    }


def _titulo_de_sistema(celulas: dict[tuple[int, int], dict[str, Any]], meta: dict[str, Any], linha_ficha: int, colunas_impressas: list[int]) -> dict[str, Any] | None:
    """Faixa de título numerado (`7.1. <Sistema>`) acima da primeira ficha; o texto é descartado."""
    mesclagens = [_intervalo(ref) for ref in meta["mesclagens"]]
    for (linha, coluna), celula in sorted(celulas.items()):
        if linha >= linha_ficha:
            break
        achado = RE_TITULO_NUMERADO.match(celula["texto"])
        if not achado:
            continue
        mescla = _celula_coberta(mesclagens, linha, coluna)
        fim = mescla[3] if mescla else coluna
        # A mesclagem pode começar numa coluna oculta; vale a primeira coluna impressa.
        visiveis = [c for c in colunas_impressas if coluna <= c <= fim]
        if not visiveis:
            continue
        return {
            "numeracao": {"capitulo": int(achado.group(1)), "formato": "{capitulo}.{indice}."},
            "coluna": get_column_letter(visiveis[0]),
            "colunas": len(visiveis),
            "altura_pt": meta["alturas"].get(linha, meta["altura_padrao"]),
            "espaco_apos_pt": sum(meta["alturas"].get(lin, meta["altura_padrao"]) for lin in range(linha + 1, linha_ficha)),
            "estilo": _estilo_persistido(celula),
        }
    return None


def _colunas_impressas(celulas: dict[tuple[int, int], dict[str, Any]], meta: dict[str, Any]) -> list[int]:
    ocultas = {indice for indice, coluna in meta["colunas"].items() if coluna["oculta"]}
    ultima = 0
    for (_linha, coluna), _celula in celulas.items():
        if coluna not in ocultas:
            ultima = max(ultima, coluna)
    for ref in meta["mesclagens"]:
        ultima = max(ultima, _intervalo(ref)[3])
    return [indice for indice in range(1, ultima + 1) if indice not in ocultas]


def _grade_de_colunas(meta: dict[str, Any], colunas_impressas: list[int], pagina: dict[str, Any]) -> dict[str, Any]:
    larguras = {
        indice: meta["colunas"].get(indice, {}).get("largura", meta.get("largura_padrao", 8.43)) for indice in colunas_impressas
    }
    largura_cm = {indice: _largura_px(largura) / DPI_TELA * POLEGADA_EM_CM for indice, largura in larguras.items()}
    if pagina["tamanho"] != "A4":
        raise LayoutExtractionError(f"Tamanho de papel {pagina['tamanho']!r} sem dimensões conhecidas (só A4 é medido).")
    papel_largura, papel_altura = PAPEL_CM[PAPER_SIZE_A4]
    if pagina["orientacao"] == "landscape":
        papel_largura, papel_altura = papel_altura, papel_largura
    util = papel_largura - pagina["margens_cm"]["esquerda"] - pagina["margens_cm"]["direita"]
    total = sum(largura_cm.values())
    escala = min(1.0, util / total) if pagina["ajustar_largura_a_pagina"] and total else 1.0
    return {
        "escala_impressao": round(escala, 4),
        "largura_util_cm": _cm(util),
        "colunas": [
            {
                "coluna": get_column_letter(indice),
                "largura_caracteres": round(larguras[indice], 2),
                "largura_cm": _cm(largura_cm[indice] * escala),
            }
            for indice in colunas_impressas
        ],
        "colunas_ocultas": [get_column_letter(i) for i, c in sorted(meta["colunas"].items()) if c["oculta"]],
    }


# ---------------------------------------------------------------- aba de resumo


def _extrair_resumo(wb_formulas: Any, nome: str, pacote: zipfile.ZipFile, membro: str, tema: list[str | None]) -> dict[str, Any]:
    """Quadro-resumo (uma linha por foto): rótulos do cabeçalho e geometria."""
    ws = wb_formulas[nome]
    cabecalho: list[dict[str, Any]] = []
    for celula in next(ws.iter_rows(min_row=1, max_row=1, max_col=MAX_COLUNAS)):
        if not hasattr(celula, "font") or celula.value is None:
            continue
        cabecalho.append({"coluna": celula.column_letter, "rotulo": _texto(celula.value), "estilo": _estilo(celula, tema)})
    corpo = None
    for celula in next(ws.iter_rows(min_row=2, max_row=2, max_col=MAX_COLUNAS)):
        if hasattr(celula, "font") and celula.value is not None:
            corpo = _estilo(celula, tema)
            break
    meta = _ler_metadados_da_aba(pacote, membro, 2)
    for coluna in cabecalho:
        indice = column_index_from_string(coluna["coluna"])
        coluna["largura_caracteres"] = meta["colunas"].get(indice, {}).get("largura")
    return {
        "aba": nome,
        "pagina": _pagina(meta) if meta["margens"] else None,
        "cabecalho": cabecalho,
        "estilo_corpo": corpo,
    }


def _aba_de_resumo(wb_formulas: Any, nome_fotografica: str) -> str | None:
    """Aba cuja coluna A referencia as fichas (`Foto nº NN`) e cujo cabeçalho é estilizado."""
    for nome in wb_formulas.sheetnames:
        if nome == nome_fotografica:
            continue
        ws = wb_formulas[nome]
        linhas = list(ws.iter_rows(min_row=1, max_row=2, max_col=MAX_COLUNAS))
        if len(linhas) < 2:
            continue
        primeira = [c for c in linhas[0] if hasattr(c, "font") and c.value is not None]
        a2 = linhas[1][0] if linhas[1] else None
        if len(primeira) >= 5 and all(c.font and c.font.b for c in primeira) and a2 is not None and RE_FOTO.match(_texto(getattr(a2, "value", None))):
            return nome
    return None


def _aba_fotografica(wb: Any, max_linhas: int) -> str:
    for nome in wb.sheetnames:
        ws = wb[nome]
        legendas = 0
        for linha in ws.iter_rows(min_row=1, max_row=max_linhas, max_col=MAX_COLUNAS, values_only=True):
            legendas += sum(1 for valor in linha if isinstance(valor, str) and RE_FOTO.match(valor))
            if legendas >= 2:
                return nome
    raise LayoutExtractionError("Nenhuma aba com fichas 'Foto nº NN' nas primeiras linhas.")


# -------------------------------------------------------------- verificação A02


def garantir_sem_dados_pessoais(valor: Any, caminho: str = "layout") -> None:
    """Falha (sem ecoar o valor) se sobrar dado pessoal em qualquer string do layout."""
    if isinstance(valor, dict):
        for chave, item in valor.items():
            if caminho == "layout" and chave == "origem":
                continue  # sha256 do arquivo: hexadecimal, não é dado pessoal
            garantir_sem_dados_pessoais(item, f"{caminho}.{chave}")
    elif isinstance(valor, (list, tuple)):
        for posicao, item in enumerate(valor):
            garantir_sem_dados_pessoais(item, f"{caminho}[{posicao}]")
    elif isinstance(valor, str):
        if RE_COR_HEX.fullmatch(valor):
            return
        for detector in (RE_EMAIL, RE_TELEFONE, RE_CPF, RE_CNPJ, RE_CEP, RE_NUMERO_LONGO):
            if detector.search(valor):
                raise LayoutExtractionError(
                    f"Dado pessoal detectado em {caminho} — o layout.json é versionado e não pode carregá-lo (A02)."
                )


# ------------------------------------------------------------------------ API


def _abrir_planilha(caminho: Path, *, data_only: bool) -> Any:
    """Workbook em modo streaming (`read_only=True`): as abas são lidas sob demanda."""
    return openpyxl.load_workbook(caminho, read_only=True, data_only=data_only, keep_links=False)


def extrair_layout(caminho_planilha: Path, *, max_linhas: int = MAX_LINHAS_PADRAO) -> dict[str, Any]:
    """Lê o original do RFIP em streaming e devolve a especificação de layout."""
    with warnings.catch_warnings():
        # A extensão x14 de validação de dados (listas suspensas) não é suportada pelo
        # openpyxl e é descartada na leitura — irrelevante para o layout.
        warnings.filterwarnings("ignore", message="Data Validation extension", category=UserWarning)
        return _extrair_layout(caminho_planilha, max_linhas)


def _extrair_layout(caminho_planilha: Path, max_linhas: int) -> dict[str, Any]:
    if not caminho_planilha.is_file():
        raise LayoutExtractionError(
            f"Original não encontrado em {caminho_planilha}. "
            "Os arquivos de 01_output-context/ ficam fora do Git — informe o caminho local."
        )
    if not zipfile.is_zipfile(caminho_planilha):
        raise LayoutExtractionError(f"{caminho_planilha.name} não é um pacote .xlsx válido.")

    with zipfile.ZipFile(caminho_planilha) as pacote:
        tema = _cores_do_tema(pacote)
        fonte_padrao = _fonte_padrao(pacote)
        partes = _partes_das_abas(pacote)

        wb = _abrir_planilha(caminho_planilha, data_only=True)
        try:
            nome_fotografica = _aba_fotografica(wb, max_linhas)
            celulas = _ler_celulas(wb[nome_fotografica], max_linhas, tema)
        finally:
            wb.close()

        membro = partes.get(nome_fotografica)
        if not membro:
            raise LayoutExtractionError(f"Parte XML da aba {nome_fotografica!r} não encontrada no pacote.")
        meta = _ler_metadados_da_aba(pacote, membro, max_linhas)
        relacoes_aba = _rels(pacote, membro)
        ancoras = _ancoras_das_fotos(pacote, relacoes_aba.get(meta.get("drawing_rid", "")), max_linhas)
        imagens_hf = _imagens_de_cabecalho(pacote, relacoes_aba.get(meta.get("vml_rid", "")))

        pagina = _pagina(meta)
        colunas_impressas = _colunas_impressas(celulas, meta)
        ficha = _montar_ficha(celulas, meta, ancoras, colunas_impressas, max_linhas)
        linha_inicial = ficha.pop("_linha_inicial")
        titulo_sistema = _titulo_de_sistema(celulas, meta, linha_inicial, colunas_impressas)

        # Tipografia de corpo = moda das células impressas da ficha com texto.
        corpo = [
            c["estilo"] for c in ficha["celulas"] if c["papel"] in ("rotulo", "valor", "descartado") and c.get("estilo", {}).get("fonte")
        ]

        # Fórmulas (não valores) para reconhecer o quadro-resumo pelos PROCV da coluna A.
        wb_formulas = _abrir_planilha(caminho_planilha, data_only=False)
        try:
            nome_resumo = _aba_de_resumo(wb_formulas, nome_fotografica)
            resumo = (
                _extrair_resumo(wb_formulas, nome_resumo, pacote, partes[nome_resumo], tema)
                if nome_resumo and partes.get(nome_resumo)
                else None
            )
        finally:
            wb_formulas.close()

    rotulos_fundo = [c["estilo"]["fundo"] for c in ficha["celulas"] if c["papel"] == "rotulo" and c.get("estilo", {}).get("fundo")]
    layout = {
        "versao_schema": 1,
        "tipo_documento": TIPO_DOCUMENTO,
        "origem": {
            "sha256": _sha256(caminho_planilha),
            "aba_fotografica": nome_fotografica,
            "aba_resumo": resumo["aba"] if resumo else None,
            "linhas_lidas": max_linhas,
        },
        "pagina": pagina,
        "tipografia": {
            "familia": _moda([c["fonte"] for c in corpo]),
            "corpo_pt": _moda([c["corpo_pt"] for c in corpo if c["corpo_pt"]]),
            "padrao_planilha": fonte_padrao,
        },
        "cores": {
            "texto": _moda([c["cor"] for c in corpo if c["cor"]], "#000000"),
            "rotulo_fundo": _moda(rotulos_fundo, None),
        },
        "grade": _grade_de_colunas(meta, colunas_impressas, pagina),
        "cabecalho": _modelar_cabecalho_rodape(meta["cabecalho"], tema, imagens_hf, "H"),
        "rodape": _modelar_cabecalho_rodape(meta["rodape"], tema, imagens_hf, "F"),
        "titulo_sistema": titulo_sistema,
        "ficha": ficha,
        "resumo": resumo,
    }
    garantir_sem_dados_pessoais(layout)
    return layout
