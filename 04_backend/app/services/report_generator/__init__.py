"""Pipeline mínimo de geração de Relatório RFO — criado para o benchmark BL-22.

Ver `rfo_pipeline` (fidelidade aproximada, sem fila assíncrona) e
`00_docs/projeto/backlog-tarefas.md` (BL-12/BL-13, bloqueadas por B-02).
"""
from app.services.report_generator.rfo_pipeline import gerar_docx, gerar_pdf, otimizar_imagem

__all__ = ["gerar_docx", "gerar_pdf", "otimizar_imagem"]
