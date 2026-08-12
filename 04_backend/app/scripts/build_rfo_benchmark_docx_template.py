"""Gera o template DOCX base (fidelidade APROXIMADA) usado pelo benchmark de
geração de relatório (BL-22, RNF-06, R-03). Roda uma única vez para produzir
`04_backend/templates/rfo_benchmark_template.docx`.

NÃO é o template fiel ao modelo original do cliente — BL-13 continua
bloqueada por B-02 (aguardando o `.docx` original do RFO, ver
`00_docs/projeto/backlog-tarefas.md`). Este arquivo existe só para viabilizar
uma medição real de tempo de geração via `docxtpl` (não usar em produção).

Uso:
    cd 04_backend
    python -m app.scripts.build_rfo_benchmark_docx_template
"""
from pathlib import Path

from docx import Document

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "templates" / "rfo_benchmark_template.docx"


def build() -> None:
    doc = Document()

    doc.add_heading("Relatório de Fiscalização de Obra (RFO)", level=1)
    doc.add_paragraph("Contrato nº {{ contrato.numero }} — {{ contrato.tipo_servico }}")
    doc.add_paragraph("Objeto: {{ contrato.objeto }}")
    doc.add_paragraph("ART de Fiscalização: {{ contrato.art_fiscalizacao }}")
    doc.add_paragraph("Edificação: {{ edificacao.nome }} — {{ edificacao.endereco }}")
    doc.add_paragraph("Engenheiro Fiscal: {{ fiscal.nome }} (CREA {{ fiscal.crea }})")
    doc.add_paragraph("Gerado em: {{ gerado_em }}")

    doc.add_heading("Visitas", level=2)
    # Bloco `{% for %}` do docxtpl abrangendo vários parágrafos — cada visita
    # tem uma quantidade variável de fotos, por isso usamos um Subdoc
    # (`visita.fotos_doc`, construído em Python) em vez de tags de imagem
    # fixas no template (ver `app/services/report_generator/rfo_pipeline.py`).
    doc.add_paragraph("{% for visita in visitas %}")
    doc.add_heading("Visita {{ visita.seq_numero }} — {{ visita.data }}", level=3)
    doc.add_paragraph("Serviços executados: {{ visita.servicos_executados }}")
    doc.add_paragraph("Observações: {{ visita.observacoes }}")
    doc.add_paragraph("{{ visita.fotos_doc }}")
    doc.add_paragraph("{% endfor %}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT_PATH))


if __name__ == "__main__":
    build()
    print(f"Template DOCX salvo em {OUTPUT_PATH}")
