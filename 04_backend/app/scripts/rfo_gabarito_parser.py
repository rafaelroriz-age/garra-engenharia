"""Parser do gabarito de sistemas prediais/subsistemas/tipos de anomalia/falha/localizações.

Fonte definitiva (premissa 6 de `00_docs/projeto/escopo.md`): `00_docs/convertidos/RFO_INSPECAO.md`,
conversão em Markdown da planilha `RFO INSPEÇÃO .xlsx`. Este módulo lê o arquivo
diretamente (sem cópia manual dos valores) para evitar erros de transcrição e
para que qualquer atualização do gabarito na fonte seja refletida ao rodar o
seed novamente (RF-10 exige dados mestre editáveis, mas a carga inicial deve
sempre corresponder à fonte).

O arquivo tem duas seções relevantes:

- `## GABARITO`: tabela "pivô" com uma coluna narrow para Sistema (Col_4) e uma
  coluna por Sistema para seus Subsistemas (apenas 13 dos 15 sistemas têm coluna
  própria na planilha original — os demais dados mestre, como Situação,
  Classificação, Tipo de Anomalia, Tipo de Falha, Grau de Risco e Localização,
  ficam em blocos verticais na coluna Col_2, um após o outro, cada um iniciado
  por um rótulo em maiúsculas).
- `## Relatório`: tabela "achatada", uma linha por foto/ocorrência registrada
  na inspeção, com colunas fixas incluindo Sistema e Subsistema. Usada apenas
  como **complemento** para os 2 sistemas (`Sistemas_Hidrossanitários` e
  `Vedações_verticais`) cuja planilha original não reservou coluna de
  Subsistema na tabela GABARITO — ver DEC-13 em `00_docs/projeto/decisoes.md`.
"""
from __future__ import annotations

from pathlib import Path

RFO_INSPECAO_MD = (
    Path(__file__).resolve().parents[3] / "00_docs" / "convertidos" / "RFO_INSPECAO.md"
)

# Colunas (1-based, correspondentes a `Col_N` da tabela GABARITO) que trazem o
# Subsistema de cada um dos 13 Sistemas com coluna própria na planilha original.
_SISTEMA_SUBSISTEMA_COLS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]

_SECOES_GABARITO_COL2 = {
    "SITUAÇÃO",
    "PRIORIDADE",
    "CLASSIFICAÇÃO",
    "TIPO DE ANOMALIA",
    "TIPO DE FALHA",
    "TIPO DE ANOMALIA / FALHA",
    "GRAU DE RISCO",
    "LOCALIZAÇÃO",
}


def _split_row(line: str) -> list[str]:
    """Divide uma linha de tabela Markdown (`| a | b | c |`) em células trimadas."""
    return [cell.strip() for cell in line.strip().split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    """Detecta a linha separadora `| --- | --- | ... |` de uma tabela Markdown."""
    return all(cell == "" or set(cell) == {"-"} for cell in cells)


def _is_column_header_row(cells: list[str]) -> bool:
    """Detecta a linha `| Col_1 | Col_2 | ... |` gerada pela conversão xlsx -> md."""
    return len(cells) > 1 and cells[1].startswith("Col_")


def _extract_section_rows(lines: list[str], section_title: str) -> list[list[str]]:
    """Retorna as linhas de dados (já divididas em células) da tabela sob `## {section_title}`.

    Ignora a linha de cabeçalho `Col_N` e a linha separadora `---`. Para de
    coletar ao encontrar a próxima seção de topo (`## `) ou uma linha em
    branco após a tabela já ter começado.
    """
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"## {section_title}":
            start = i
            break
    if start is None:
        raise ValueError(f"Seção '## {section_title}' não encontrada em {RFO_INSPECAO_MD}")

    rows: list[list[str]] = []
    started = False
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if not stripped.startswith("|"):
            if started:
                break
            continue
        cells = _split_row(stripped)
        if _is_separator_row(cells) or _is_column_header_row(cells):
            continue
        started = True
        rows.append(cells)
    return rows


def _read_lines() -> list[str]:
    if not RFO_INSPECAO_MD.exists():
        raise FileNotFoundError(f"Gabarito não encontrado: {RFO_INSPECAO_MD}")
    return RFO_INSPECAO_MD.read_text(encoding="utf-8").splitlines()


def parse_gabarito() -> dict[str, object]:
    """Extrai do bloco `## GABARITO` os dados mestre do sistema.

    Retorna um dict com:
    - `sistemas`: lista ordenada dos 15 nomes de Sistema Predial.
    - `subsistemas_por_sistema`: dict sistema -> lista ordenada de subsistemas
      (vazia para os sistemas sem coluna própria na planilha original).
    - `tipos_anomalia`, `tipos_falha`, `localizacoes`: listas ordenadas.
    """
    rows = _extract_section_rows(_read_lines(), "GABARITO")

    header_row = next((r for r in rows if len(r) > 4 and r[4] == "Sistema"), None)
    if header_row is None:
        raise ValueError("Linha de cabeçalho ('Sistema' na Col_4) não encontrada no GABARITO")

    col_to_sistema: dict[int, str] = {
        col: header_row[col]
        for col in _SISTEMA_SUBSISTEMA_COLS
        if len(header_row) > col and header_row[col]
    }

    sistemas: list[str] = []
    subsistemas_por_sistema: dict[str, list[str]] = {}
    tipos_anomalia: list[str] = []
    tipos_falha: list[str] = []
    localizacoes: list[str] = []

    current_section: str | None = None

    for cells in rows:
        col2 = cells[2] if len(cells) > 2 else ""
        col4 = cells[4] if len(cells) > 4 else ""
        is_header_row = col4 == "Sistema"

        if col2 in _SECOES_GABARITO_COL2:
            current_section = col2
        elif col2 and not is_header_row:
            if current_section == "TIPO DE ANOMALIA" and col2 not in tipos_anomalia:
                tipos_anomalia.append(col2)
            elif current_section == "TIPO DE FALHA" and col2 not in tipos_falha:
                tipos_falha.append(col2)
            elif current_section == "LOCALIZAÇÃO" and col2 not in localizacoes:
                localizacoes.append(col2)

        if col4 and not is_header_row:
            if col4 not in sistemas:
                sistemas.append(col4)
            subsistemas_por_sistema.setdefault(col4, [])

        if not is_header_row:
            for col, sistema_nome in col_to_sistema.items():
                valor = cells[col] if len(cells) > col else ""
                if not valor:
                    continue
                lista = subsistemas_por_sistema.setdefault(sistema_nome, [])
                if valor not in lista:
                    lista.append(valor)

    return {
        "sistemas": sistemas,
        "subsistemas_por_sistema": subsistemas_por_sistema,
        "tipos_anomalia": tipos_anomalia,
        "tipos_falha": tipos_falha,
        "localizacoes": localizacoes,
    }


def parse_relatorio_subsistemas_por_sistema() -> dict[str, list[str]]:
    """Extrai do bloco `## Relatório` os pares (Sistema, Subsistema) realmente utilizados.

    Usado apenas como complemento para sistemas sem coluna de Subsistema na
    tabela GABARITO (ver módulo docstring).
    """
    rows = _extract_section_rows(_read_lines(), "Relatório")

    result: dict[str, list[str]] = {}
    for cells in rows:
        if len(cells) <= 10:
            continue
        sistema = cells[9]
        subsistema = cells[10]
        if not sistema or sistema == "Sistema" or not subsistema:
            continue
        lista = result.setdefault(sistema, [])
        if subsistema not in lista:
            lista.append(subsistema)
    return result


def build_gabarito() -> dict[str, object]:
    """Combina `## GABARITO` (fonte principal) com `## Relatório` (complemento).

    Para sistemas cuja tabela GABARITO não trouxe nenhum subsistema, usa os
    subsistemas efetivamente registrados nas ocorrências do `## Relatório`
    (mesma fonte `RFO_INSPECAO.md`, sem inventar valores).
    """
    gabarito = parse_gabarito()
    subsistemas_por_sistema: dict[str, list[str]] = gabarito["subsistemas_por_sistema"]  # type: ignore[assignment]

    usados = parse_relatorio_subsistemas_por_sistema()
    for sistema, subsistemas_usados in usados.items():
        atuais = subsistemas_por_sistema.setdefault(sistema, [])
        if atuais:
            continue  # GABARITO já trouxe subsistemas para este sistema; não complementar
        for subsistema in subsistemas_usados:
            if subsistema not in atuais:
                atuais.append(subsistema)

    return gabarito
