"""Pipelines de geração de relatório: RFO (`rfo_pipeline`) e LTIP (`ltip_pipeline`).

Ver `00_docs/projeto/backlog-tarefas.md` (BL-12/BL-13 para o RFO, BL-17 para o LTIP).

Os atalhos `gerar_docx`, `gerar_pdf` e `otimizar_imagem` (do RFO) são
resolvidos sob demanda (PEP 562): `rfo_pipeline` importa `weasyprint` no topo
e, importado aqui de forma ansiosa, impediria carregar `ltip_pipeline` fora do
container (GTK/Pango ausentes no Windows).
"""
from __future__ import annotations

from typing import Any

__all__ = ["gerar_docx", "gerar_pdf", "otimizar_imagem"]


def __getattr__(nome: str) -> Any:
    if nome == "otimizar_imagem":  # sem WeasyPrint (V1-02)
        from app.services.report_generator.imagem import otimizar_imagem

        return otimizar_imagem
    if nome in __all__:
        from app.services.report_generator import rfo_pipeline

        return getattr(rfo_pipeline, nome)
    raise AttributeError(f"module {__name__!r} has no attribute {nome!r}")
