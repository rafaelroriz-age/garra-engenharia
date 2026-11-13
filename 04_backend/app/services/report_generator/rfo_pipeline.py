"""Pipeline de geração de Relatório RFO (PDF via WeasyPrint, DOCX via docxtpl).

Os templates consumidos aqui são os derivados do original do cliente
(`templates/rfo/`), produzidos por `python -m app.scripts.build_rfo_templates`
a partir de `templates/rfo/layout.json` — ADR-13/DEC-25, BL-12/BL-13.

A fila assíncrona Celery/Redis do ADR-06 continua pendente: este módulo expõe
apenas as funções de renderização síncronas consumidas pelos scripts de
benchmark (BL-22) e pelo futuro worker.
"""
from __future__ import annotations

import base64
import copy
import io
import re
import time
from pathlib import Path
from typing import Any

from docx.shared import Mm
from docxtpl import DocxTemplate
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.services.report_generator.foto_fetcher import (
    RegistroDeFotos,
    criar_url_fetcher,
    mime_da_imagem,
)
from app.services.report_generator.imagem import otimizar_imagem  # noqa: F401 — re-export (V1-02)
from app.services.report_generator.legenda_foto import legenda_para_relatorio

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
RFO_TEMPLATES_DIR = TEMPLATES_DIR / "rfo"
HTML_TEMPLATE_NAME = "rfo/rfo_template.html.j2"
DOCX_TEMPLATE_NAME = "rfo/rfo_template.docx"
# Marca vetorizada com fundo transparente (RN-07/B-02), gerada por
# `python -m app.scripts.build_brand_assets`. O DOCX não aceita SVG e já traz
# o PNG equivalente embutido no próprio template.
LOGO_SVG_PATH = TEMPLATES_DIR / "assets" / "logo-garra.svg"


def _em_itens(texto: str | None) -> list[str]:
    """Quebra um campo de texto livre em itens (uma constatação por linha)."""
    if not texto:
        return []
    return [item.strip() for item in re.split(r"[\r\n]+", texto) if item.strip()]


def _logo_data_uri() -> str | None:
    if not LOGO_SVG_PATH.is_file():
        return None
    return "data:image/svg+xml;base64," + base64.b64encode(LOGO_SVG_PATH.read_bytes()).decode("ascii")


def normalizar_contexto(contexto: dict[str, Any]) -> dict[str, Any]:
    """Completa o contexto com o que o template derivado espera.

    Mantém compatível qualquer chamador que monte apenas os campos básicos
    (contrato/edificacao/fiscal/visitas), sem duplicar essa lógica em cada um.
    """
    normalizado = copy.deepcopy(contexto)
    normalizado.setdefault("executores", [])
    normalizado.setdefault("nbrs", [])
    normalizado.setdefault("logo_data_uri", _logo_data_uri())
    for visita in normalizado.get("visitas", []):
        visita.setdefault("servicos_executados_lista", _em_itens(visita.get("servicos_executados")))
        visita.setdefault("observacoes_lista", _em_itens(visita.get("observacoes")))
    return normalizado


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
    # para gerar o DOCX) ao anexar a referência de cada foto. As fotos vão ao
    # WeasyPrint por `url_fetcher` (DEC-41); sem ele, caem para data URI base64.
    registro = RegistroDeFotos()
    fetcher = criar_url_fetcher(registro)
    contexto_html = normalizar_contexto(contexto)
    for visita in contexto_html["visitas"]:
        for foto in visita["fotos"]:
            conteudo = fotos_bytes[foto["storage_key"]]
            if fetcher:
                foto["data_uri"] = registro.registrar(conteudo)
            else:
                b64 = base64.b64encode(conteudo).decode("ascii")
                foto["data_uri"] = f"data:{mime_da_imagem(conteudo)};base64,{b64}"
            # DEC-37 DP-9: o template imprime `foto.legenda`; IA nunca entra.
            foto["legenda"] = legenda_para_relatorio(foto)

    inicio_render = time.perf_counter()
    html_renderizado = template.render(**contexto_html)
    fim_render = time.perf_counter()

    opcoes = {"url_fetcher": fetcher} if fetcher else {}
    documento = HTML(string=html_renderizado, base_url=str(TEMPLATES_DIR), **opcoes).render()
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
    contexto_docx = normalizar_contexto(contexto)

    inicio_subdocs = time.perf_counter()
    visitas_ctx = []
    for visita in contexto_docx["visitas"]:
        subdoc = tpl.new_subdoc()
        for foto in visita["fotos"]:
            subdoc.add_picture(io.BytesIO(fotos_bytes[foto["storage_key"]]), width=Mm(90))
            legenda = legenda_para_relatorio(foto)
            if legenda:
                subdoc.add_paragraph(legenda)
        visitas_ctx.append({**visita, "fotos_doc": subdoc})
    fim_subdocs = time.perf_counter()

    render_ctx = {**contexto_docx, "visitas": visitas_ctx}
    tpl.render(render_ctx)
    tpl.save(str(destino))
    fim_render = time.perf_counter()

    return {
        "montagem_subdocs": fim_subdocs - inicio_subdocs,
        "render_e_salvar": fim_render - fim_subdocs,
        "total": fim_render - inicio_subdocs,
        "tamanho_bytes": destino.stat().st_size,
    }
