"""Pipeline mínimo de geração de Relatório RFO (PDF via WeasyPrint, DOCX via docxtpl).

Criado para viabilizar o benchmark de BL-22 (RNF-06, R-03). BL-12/BL-13
(fidelidade final ao template do cliente + fila assíncrona Celery/Redis do
ADR-06) continuam bloqueadas por B-02 — este módulo usa templates de
fidelidade APROXIMADA (não o modelo original do cliente) só para produzir uma
medição real e reproduzível de tempo de geração. Não deve ser tratado como a
implementação definitiva de BL-12/BL-13.
"""
from __future__ import annotations

import base64
import copy
import io
import time
from pathlib import Path
from typing import Any

from docx.shared import Mm
from docxtpl import DocxTemplate
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
HTML_TEMPLATE_NAME = "rfo_template.html.j2"
DOCX_TEMPLATE_NAME = "rfo_benchmark_template.docx"


def otimizar_imagem(conteudo: bytes, *, max_lado: int = 1200, qualidade: int = 72) -> bytes:
    """Redimensiona (se necessário) e recomprime uma foto para uso em relatório.

    Mitiga o gargalo identificado no benchmark de BL-22: `app.services.image_processing`
    (BL-11) recodifica a imagem no upload mas NUNCA a redimensiona — fotos de
    câmera de celular em resolução total (vários MB) hoje são embutidas em
    PDF/DOCX sem nenhuma redução prévia.
    """
    imagem = Image.open(io.BytesIO(conteudo)).convert("RGB")
    if max(imagem.size) > max_lado:
        escala = max_lado / max(imagem.size)
        novo_tamanho = (max(1, int(imagem.width * escala)), max(1, int(imagem.height * escala)))
        imagem = imagem.resize(novo_tamanho, Image.LANCZOS)
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG", quality=qualidade, optimize=True)
    return buffer.getvalue()


def gerar_pdf(contexto: dict[str, Any], fotos_bytes: dict[str, bytes], destino: Path) -> dict[str, float]:
    """Renderiza o HTML (Jinja2) e converte para PDF (WeasyPrint).

    Retorna um dict com o tempo (segundos) de cada etapa: `render_html`,
    `conversao_pdf` e `total`, além de `n_paginas` e `tamanho_bytes`.
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template(HTML_TEMPLATE_NAME)

    # Cópia profunda: evita mutar o `contexto` original (reaproveitado depois
    # para gerar o DOCX) ao anexar o data URI base64 de cada foto.
    contexto_html = copy.deepcopy(contexto)
    for visita in contexto_html["visitas"]:
        for foto in visita["fotos"]:
            b64 = base64.b64encode(fotos_bytes[foto["storage_key"]]).decode("ascii")
            foto["data_uri"] = f"data:image/jpeg;base64,{b64}"

    inicio_render = time.perf_counter()
    html_renderizado = template.render(**contexto_html)
    fim_render = time.perf_counter()

    documento = HTML(string=html_renderizado, base_url=str(TEMPLATES_DIR)).render()
    n_paginas = len(documento.pages)
    documento.write_pdf(str(destino))
    fim_pdf = time.perf_counter()

    return {
        "render_html": fim_render - inicio_render,
        "conversao_pdf": fim_pdf - fim_render,
        "total": fim_pdf - inicio_render,
        "n_paginas": n_paginas,
        "tamanho_bytes": destino.stat().st_size,
    }


def gerar_docx(contexto: dict[str, Any], fotos_bytes: dict[str, bytes], destino: Path) -> dict[str, float]:
    """Renderiza o DOCX (docxtpl) a partir do template base.

    Retorna um dict com o tempo (segundos) de cada etapa: `montagem_subdocs`,
    `render_e_salvar` e `total`, além de `tamanho_bytes`.
    """
    template_path = TEMPLATES_DIR / DOCX_TEMPLATE_NAME
    tpl = DocxTemplate(str(template_path))

    inicio_subdocs = time.perf_counter()
    visitas_ctx = []
    for visita in contexto["visitas"]:
        subdoc = tpl.new_subdoc()
        for foto in visita["fotos"]:
            subdoc.add_picture(io.BytesIO(fotos_bytes[foto["storage_key"]]), width=Mm(90))
            if foto.get("legenda"):
                subdoc.add_paragraph(foto["legenda"])
        visitas_ctx.append({**visita, "fotos_doc": subdoc})
    fim_subdocs = time.perf_counter()

    render_ctx = {**contexto, "visitas": visitas_ctx}
    tpl.render(render_ctx)
    tpl.save(str(destino))
    fim_render = time.perf_counter()

    return {
        "montagem_subdocs": fim_subdocs - inicio_subdocs,
        "render_e_salvar": fim_render - fim_subdocs,
        "total": fim_render - inicio_subdocs,
        "tamanho_bytes": destino.stat().st_size,
    }
