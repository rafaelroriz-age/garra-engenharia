r"""Build a DOCX Jinja template from the reviewed contract markdown.

Usage (from 04_backend/):
    .venv\Scripts\python.exe -m app.scripts.build_contract_template_docx
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[2]
SOURCE_MD = ROOT.parent / "01_output-context" / "Contrato_Revisado_Garra_Software.md"
TARGET_DOCX = ROOT / "templates" / "contracts" / "contrato_revisado_template.docx"
TARGET_GUIDE = ROOT / "templates" / "contracts" / "contrato_revisado_template.placeholders.md"


PLACEHOLDER_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        "**EMPRESA.**, inscrita no CNPJ nº CNPJ, com sede na ENDEREÇO, Aparecida de Goiânia/GO, neste ato representada por Roniel Ribeiro Costa, doravante denominada **CONTRATANTE**; e, de outro lado, **CONTRATADO**, inscrito no CNPJ nº NUMERO CNPJ com sede na ENDEREÇO, neste ato representado por NOME, doravante denominado **CONTRATADO**;",
        "**{{ contratante_razao_social }}**, inscrita no CNPJ nº {{ contratante_cnpj }}, com sede na {{ contratante_endereco }}, {{ contratante_cidade_uf }}, neste ato representada por {{ contratante_representante_nome }}, doravante denominada **CONTRATANTE**; e, de outro lado, **{{ contratado_razao_social }}**, inscrito no CNPJ nº {{ contratado_cnpj }} com sede na {{ contratado_endereco }}, neste ato representado por {{ contratado_representante_nome }}, doravante denominado **CONTRATADO**;",
    ),
    ("INSERIR DATA OU PRAZO FINAL", "{{ prazo_entrega_final }}"),
    ("INSERIR PRAZO", "{{ prazo_correcao_nao_conformidades }}"),
    ("INSERIR DIA", "{{ dia_vencimento_parcela }}"),
    ("INSERIR FREQUÊNCIA", "{{ backup_frequencia }}"),
    ("INSERIR PERCENTUAL", "{{ disponibilidade_minima_percentual }}"),
    ("INSERIR INFORMAÇÃO", "{{ info_preenchimento }}"),
    ("INSERIR DATA.", "{{ data_assinatura_extenso }}."),
    ("INSERIR DATA", "{{ data_generica }}"),
    ("INSERIR CRITÉRIO OBJETIVO", "{{ criterio_aceite_objetivo }}"),
    ("INSERIR NAVEGADORES E DISPOSITIVOS", "{{ navegadores_dispositivos_suportados }}"),
    ("INSERIR QUANTIDADE/TAMANHO", "{{ volume_fotos_documentos }}"),
    ("INSERIR QUANTIDADE", "{{ quantidade_usuarios_estimados }}"),
    ("INSERIR FORMATOS", "{{ formatos_exportacao_portabilidade }}"),
    ("Aparecida de Goiânia/GO", "{{ cidade_assinatura }}"),
)


def apply_replacements(text: str) -> str:
    updated = text
    for original, replacement in PLACEHOLDER_REPLACEMENTS:
        updated = updated.replace(original, replacement)
    return updated


def flush_table(document: Document, table_lines: list[str]) -> None:
    if not table_lines:
        return

    rows: list[list[str]] = []
    for raw in table_lines:
        if not raw.startswith("|"):
            continue
        parts = [col.strip() for col in raw.strip().strip("|").split("|")]
        if not parts:
            continue
        # Skip markdown separator row like | --- | --- |
        if all(part.replace(":", "").replace("-", "") == "" for part in parts):
            continue
        rows.append(parts)

    if not rows:
        return

    max_cols = max(len(row) for row in rows)
    table = document.add_table(rows=len(rows), cols=max_cols)
    table.style = "Table Grid"

    for r_idx, row in enumerate(rows):
        for c_idx in range(max_cols):
            value = row[c_idx] if c_idx < len(row) else ""
            table.rows[r_idx].cells[c_idx].text = apply_replacements(value)


def build_docx_from_markdown(source_md: Path, target_docx: Path) -> None:
    document = Document()
    table_buffer: list[str] = []

    for raw_line in source_md.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()

        if line.startswith("|"):
            table_buffer.append(line)
            continue

        if table_buffer:
            flush_table(document, table_buffer)
            table_buffer = []

        if not line.strip():
            document.add_paragraph("")
            continue

        text = apply_replacements(line)
        stripped = text.strip()

        if stripped.startswith("# "):
            document.add_heading(stripped[2:].strip(), level=1)
        elif stripped.startswith("## "):
            document.add_heading(stripped[3:].strip(), level=2)
        elif stripped.startswith("### "):
            document.add_heading(stripped[4:].strip(), level=3)
        elif stripped.startswith("- "):
            document.add_paragraph(stripped[2:].strip(), style="List Bullet")
        else:
            document.add_paragraph(stripped)

    if table_buffer:
        flush_table(document, table_buffer)

    target_docx.parent.mkdir(parents=True, exist_ok=True)
    document.save(target_docx)


def write_placeholder_guide(target_guide: Path) -> None:
    lines = [
        "# Placeholders do Template de Contrato",
        "",
        "Este arquivo lista os campos Jinja2 usados em `contrato_revisado_template.docx`.",
        "Use com `docxtpl` no backend para renderização do documento final.",
        "",
        "## Campos",
    ]

    keys = sorted(
        {
            key
            for _, replacement in PLACEHOLDER_REPLACEMENTS
            for key in re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replacement)
        }
    )
    for key in keys:
        lines.append(f"- `{key}`")

    target_guide.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not SOURCE_MD.exists():
        raise FileNotFoundError(f"Arquivo fonte não encontrado: {SOURCE_MD}")

    build_docx_from_markdown(SOURCE_MD, TARGET_DOCX)
    write_placeholder_guide(TARGET_GUIDE)

    print(f"Template DOCX criado em: {TARGET_DOCX}")
    print(f"Guia de placeholders criado em: {TARGET_GUIDE}")


if __name__ == "__main__":
    main()
