"""Extração determinística do layout do RFO a partir da planilha original do cliente.

Implementa a primeira metade de ADR-13/DEC-25 (`00_docs/arquitetura.md`): em vez de
transcrever o layout manualmente (não reprodutível, não auditável), lê o
`.xlsx`/`.xlsm` original com `openpyxl` e produz um artefato intermediário
(`templates/rfo/layout.json`) do qual derivam tanto o `.html.j2` do WeasyPrint
quanto o `.docx` do docxtpl — garantindo que PDF e DOCX não divirjam.

O `.xlsm` é apenas LIDO, nunca executado: `keep_vba=False` descarta as macros
antes de qualquer processamento (OWASP A08).

Os originais ficam em `01_output-context/`, fora do controle de versão
(`.gitignore`); o caminho é sempre recebido por parâmetro e a ausência do
arquivo falha explicitamente.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

POLEGADA_EM_CM = 2.54
#: `page_setup.paperSize` do OOXML — 9 é A4.
PAPER_SIZE_A4 = 9
RE_FOTO = re.compile(r"^\s*foto\s*(\d+)\s*$", re.IGNORECASE)
RE_ASSINATURA = re.compile(r"_{5,}")
#: Linhas do topo que pertencem à marca do emitente (endereço/contato da Garra),
#: e não aos dados variáveis do contrato preenchidos naquele exemplar.
RE_CONTATO_EMITENTE = re.compile(r"CEP\b|@|Qd\.", re.IGNORECASE)


class LayoutExtractionError(RuntimeError):
    """Erro irrecuperável ao ler o original — nunca degrada para valor inventado."""


@dataclass
class Secao:
    """Cabeçalho de seção da planilha (célula em negrito com preenchimento sólido)."""

    titulo: str
    linha: int
    celula: str
    campos: list[dict[str, Any]] = field(default_factory=list)


def _cor_do_tema(theme: int | None, tint: float | None) -> str | None:
    """Converte cor de tema do Excel em hexadecimal.

    Só resolve os dois temas neutros usados no RFO (0 = background claro,
    1 = texto escuro); qualquer outro retorna ``None`` em vez de chutar um valor.
    """
    if theme is None:
        return None
    base = {0: 0xFF, 1: 0x00}.get(theme)
    if base is None:
        return None
    fator = tint or 0.0
    if fator < 0:
        canal = round(base * (1 + fator))
    else:
        canal = round(base + (255 - base) * fator)
    canal = max(0, min(255, canal))
    return f"#{canal:02X}{canal:02X}{canal:02X}"


def _cor_da_celula(celula: Any) -> str | None:
    preenchimento = celula.fill
    if not preenchimento or preenchimento.fill_type != "solid":
        return None
    cor = preenchimento.start_color
    rgb = cor.rgb if isinstance(cor.rgb, str) else None
    if rgb and len(rgb) == 8:
        return f"#{rgb[2:]}"
    return _cor_do_tema(cor.theme if isinstance(cor.theme, int) else None, cor.tint)


def _texto(valor: Any) -> str:
    return " ".join(str(valor).split()) if valor is not None else ""


def _e_cabecalho_de_secao(celula: Any) -> bool:
    return bool(celula.value) and bool(celula.font and celula.font.bold) and _cor_da_celula(celula) is not None


def _proximo_valor_na_linha(ws: Worksheet, linha: int, coluna_inicial: int, coluna_final: int) -> str | None:
    """Coordenada da célula de valor à direita de um rótulo, na mesma linha.

    Para quando encontra outro rótulo (célula em negrito terminada em `:`) — sem
    isso, um campo vazio no exemplar usado como referência tomaria emprestada a
    coordenada do campo seguinte.
    """
    for coluna in range(coluna_inicial + 1, coluna_final + 1):
        celula = ws.cell(row=linha, column=coluna)
        if celula.value is None:
            continue
        texto = _texto(celula.value)
        if celula.font and celula.font.bold and texto.endswith(":"):
            return None
        return celula.coordinate
    return None


def _extrair_secoes(ws: Worksheet, coluna_final: int) -> list[Secao]:
    """Percorre a aba de cima para baixo agrupando rótulos sob o cabeçalho vigente."""
    secoes: list[Secao] = []
    atual: Secao | None = None
    for linha in range(1, ws.max_row + 1):
        for coluna in range(1, coluna_final + 1):
            celula = ws.cell(row=linha, column=coluna)
            if celula.value is None:
                continue
            texto = _texto(celula.value)
            if not texto:
                continue
            if _e_cabecalho_de_secao(celula):
                atual = Secao(titulo=texto, linha=linha, celula=celula.coordinate)
                secoes.append(atual)
                break
            if atual is None or not (celula.font and celula.font.bold):
                continue
            if not texto.endswith(":"):
                continue
            # Apenas a geometria é persistida: o conteúdo preenchido no exemplar do
            # cliente (CPF, e-mails, nomes) nunca entra no layout.json versionado.
            atual.campos.append(
                {
                    "rotulo": texto,
                    "celula_rotulo": celula.coordinate,
                    "celula_valor": _proximo_valor_na_linha(ws, linha, coluna, coluna_final),
                }
            )
    return secoes


def _extrair_grade_fotografica(ws: Worksheet) -> dict[str, Any]:
    """Deriva a geometria do registro fotográfico a partir das legendas ``Foto NN``."""
    marcadores: list[tuple[int, int, int]] = []
    for linha in ws.iter_rows(min_row=1, max_row=ws.max_row):
        for celula in linha:
            if celula.value is None:
                continue
            achado = RE_FOTO.match(str(celula.value))
            if achado:
                marcadores.append((int(achado.group(1)), celula.row, celula.column))
    if not marcadores:
        return {"encontrado": False}

    marcadores.sort()
    linhas = sorted({linha for _, linha, _ in marcadores})
    colunas = sorted({coluna for _, _, coluna in marcadores})
    espacamentos = {b - a for a, b in pairwise(linhas) if b - a > 0}
    return {
        "encontrado": True,
        "total_no_original": len(marcadores),
        "fotos_por_linha": len(colunas),
        "colunas_inicio": [get_column_letter(coluna) for coluna in colunas],
        "linhas_legenda": linhas,
        # Espaçamento vertical mínimo entre duas faixas de fotos = altura da célula da foto.
        "linhas_por_foto": min(espacamentos) if espacamentos else None,
        "prefixo_legenda": "Foto",
    }


def _extrair_assinaturas(ws: Worksheet) -> list[str]:
    assinaturas: list[str] = []
    for linha in ws.iter_rows(min_row=1, max_row=ws.max_row):
        for celula in linha:
            if celula.value is None or not RE_ASSINATURA.search(str(celula.value)):
                continue
            rotulo = " / ".join(
                parte.strip() for parte in str(celula.value).splitlines() if parte.strip() and not RE_ASSINATURA.match(parte.strip())
            )
            # O bloco de assinaturas se repete a cada página de impressão do modelo.
            if rotulo and rotulo not in assinaturas:
                assinaturas.append(rotulo)
    return assinaturas


def _extrair_cabecalho(ws: Worksheet) -> dict[str, Any]:
    """Faixa de marca no topo: título grande, endereço e logo ancorada."""
    titulo = {"texto": None, "fonte_pt": None}
    linhas_extras: list[str] = []
    for linha in ws.iter_rows(min_row=1, max_row=8):
        for celula in linha:
            if celula.value is None:
                continue
            texto = _texto(celula.value)
            if not texto:
                continue
            tamanho = celula.font.size if celula.font else None
            if tamanho and tamanho >= 24 and titulo["texto"] is None:
                titulo = {"texto": texto, "fonte_pt": float(tamanho)}
            elif RE_CONTATO_EMITENTE.search(texto):
                linhas_extras.append(texto)
    logos = []
    for imagem in getattr(ws, "_images", []):
        ancora = getattr(imagem.anchor, "_from", None)
        if ancora is not None and ancora.row < 8:
            logos.append(
                {
                    "coluna": get_column_letter(ancora.col + 1),
                    "linha": ancora.row + 1,
                    "largura_px": imagem.width,
                    "altura_px": imagem.height,
                }
            )
    return {"titulo": titulo, "linhas_texto": linhas_extras, "logos": logos}


def _extrair_pagina(ws: Worksheet) -> dict[str, Any]:
    margens = ws.page_margins
    quebras = [brk.id for brk in ws.row_breaks.brk] if ws.row_breaks else []
    return {
        "tamanho": "A4" if ws.page_setup.paperSize in (None, PAPER_SIZE_A4) else str(ws.page_setup.paperSize),
        "orientacao": ws.page_setup.orientation or "portrait",
        "area_impressao": ws.print_area,
        "quebras_de_linha": quebras,
        "margens_cm": {
            "esquerda": round((margens.left or 0) * POLEGADA_EM_CM, 2),
            "direita": round((margens.right or 0) * POLEGADA_EM_CM, 2),
            "superior": round((margens.top or 0) * POLEGADA_EM_CM, 2),
            "inferior": round((margens.bottom or 0) * POLEGADA_EM_CM, 2),
        },
    }


def _extrair_tipografia(ws: Worksheet) -> dict[str, Any]:
    """Fonte/corpo predominante das células com conteúdo (moda simples)."""
    contagem_familia: dict[str, int] = {}
    contagem_corpo: dict[float, int] = {}
    for linha in ws.iter_rows(min_row=1, max_row=ws.max_row):
        for celula in linha:
            if celula.value is None or not celula.font:
                continue
            if celula.font.name:
                contagem_familia[celula.font.name] = contagem_familia.get(celula.font.name, 0) + 1
            if celula.font.size:
                tamanho = float(celula.font.size)
                contagem_corpo[tamanho] = contagem_corpo.get(tamanho, 0) + 1
    if not contagem_familia or not contagem_corpo:
        raise LayoutExtractionError(f"Aba {ws.title!r} não tem nenhuma célula com fonte definida.")
    return {
        "familia": max(contagem_familia.items(), key=lambda item: item[1])[0],
        "corpo_pt": max(contagem_corpo.items(), key=lambda item: item[1])[0],
    }


def _largura_colunas(ws: Worksheet, coluna_final: int) -> dict[str, float]:
    larguras: dict[str, float] = {}
    for indice in range(1, coluna_final + 1):
        letra = get_column_letter(indice)
        dimensao = ws.column_dimensions.get(letra)
        # 8.43 é a largura padrão do Excel quando a coluna nunca foi redimensionada.
        larguras[letra] = round(dimensao.width, 2) if dimensao and dimensao.width else 8.43
    return larguras


def _cor_predominante_das_secoes(ws: Worksheet, secoes: list[Secao]) -> str | None:
    for secao in secoes:
        cor = _cor_da_celula(ws[secao.celula])
        if cor:
            return cor
    return None


def _coluna_final_impressa(ws: Worksheet, padrao: int) -> int:
    """Última coluna dentro da área de impressão (o resto é rascunho fora do papel)."""
    area = ws.print_area
    if not area:
        return padrao
    achado = re.search(r"\$([A-Z]+)\$\d+$", area[0] if isinstance(area, list) else area)
    if not achado:
        return padrao
    from openpyxl.utils import column_index_from_string

    return column_index_from_string(achado.group(1))


def _sha256(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _serializar_secoes(secoes: list[Secao]) -> list[dict[str, Any]]:
    """Serializa mantendo a primeira ocorrência de cada título.

    Seções como "REGISTRO FOTOGRÁFICO" se repetem a cada página de impressão do
    modelo; no template elas viram um único bloco iterado.
    """
    vistos: set[str] = set()
    serializadas: list[dict[str, Any]] = []
    for secao in secoes:
        if secao.titulo in vistos:
            continue
        vistos.add(secao.titulo)
        serializadas.append({"titulo": secao.titulo, "linha": secao.linha, "celula": secao.celula, "campos": secao.campos})
    return serializadas


def extrair_layout(caminho_planilha: Path, *, aba_capa: str | None = None, prefixo_aba_visita: str = "Dia") -> dict[str, Any]:
    """Lê o original do RFO e devolve a especificação de layout como dicionário.

    `aba_capa` default = primeira aba do arquivo (no original é "Informações Gerais");
    abas de visita são as que começam com `prefixo_aba_visita`.
    """
    if not caminho_planilha.is_file():
        raise LayoutExtractionError(
            f"Original não encontrado em {caminho_planilha}. "
            "Os arquivos de 01_output-context/ ficam fora do Git — informe o caminho local."
        )

    workbook = openpyxl.load_workbook(caminho_planilha, data_only=True, keep_vba=False)
    try:
        capa_nome = aba_capa or workbook.sheetnames[0]
        if capa_nome not in workbook.sheetnames:
            raise LayoutExtractionError(f"Aba de capa {capa_nome!r} inexistente em {caminho_planilha.name}.")
        abas_visita = [nome for nome in workbook.sheetnames if nome.lower().startswith(prefixo_aba_visita.lower())]
        if not abas_visita:
            raise LayoutExtractionError(
                f"Nenhuma aba de visita (prefixo {prefixo_aba_visita!r}) em {caminho_planilha.name}."
            )

        capa = workbook[capa_nome]
        visita = workbook[abas_visita[0]]

        coluna_final_capa = _coluna_final_impressa(capa, capa.max_column)
        coluna_final_visita = _coluna_final_impressa(visita, visita.max_column)

        secoes_capa = _extrair_secoes(capa, coluna_final_capa)
        secoes_visita = _extrair_secoes(visita, coluna_final_visita)

        return {
            "versao_schema": 1,
            "tipo_documento": "RFO",
            "origem": {
                "arquivo": caminho_planilha.name,
                "sha256": _sha256(caminho_planilha),
                "aba_capa": capa_nome,
                "abas_visita": abas_visita,
            },
            "pagina": _extrair_pagina(visita),
            "tipografia": {
                **_extrair_tipografia(visita),
                "titulo_pt": _extrair_cabecalho(visita)["titulo"]["fonte_pt"],
            },
            "cores": {
                "cabecalho_secao_fundo": _cor_predominante_das_secoes(visita, secoes_visita) or "#D9D9D9",
                "texto": "#000000",
            },
            "cabecalho": _extrair_cabecalho(visita),
            "capa": {
                "aba": capa_nome,
                "colunas": _largura_colunas(capa, coluna_final_capa),
                "secoes": _serializar_secoes(secoes_capa),
            },
            "visita": {
                "aba_modelo": abas_visita[0],
                "colunas": _largura_colunas(visita, coluna_final_visita),
                "secoes": _serializar_secoes(secoes_visita),
                "registro_fotografico": _extrair_grade_fotografica(visita),
                "assinaturas": _extrair_assinaturas(visita),
            },
        }
    finally:
        workbook.close()
