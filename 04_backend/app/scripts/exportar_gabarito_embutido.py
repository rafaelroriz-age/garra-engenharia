"""Exporta o gabarito parseado de RFO_INSPECAO.md para app/data/gabarito_rfo.json (DEC-51).

Uso (a partir de 04_backend): python -m app.scripts.exportar_gabarito_embutido
Saída determinística: UTF-8, indent=2, chaves ordenadas, sem timestamps.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.scripts.rfo_gabarito_parser import GABARITO_EMBUTIDO_JSON, build_gabarito_from_markdown


def exportar(destino: Path = GABARITO_EMBUTIDO_JSON) -> Path:
    gabarito = build_gabarito_from_markdown()
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(gabarito, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    destino.write_text(texto, encoding="utf-8", newline="\n")
    return destino


if __name__ == "__main__":
    print(f"Gabarito exportado para {exportar()}")
