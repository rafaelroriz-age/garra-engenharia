"""Pipeline de geração do RFIP — Relatório Fotográfico de Inspeção Predial (BL-12, DEC-36).

Irmão de `ltip_pipeline` e `vistoria_cautelar_pipeline`: mesma API
(`renderizar_html`, `gerar_pdf`, `gerar_docx`, com `contexto` + `fotos_bytes`
indexado por `storage_key` + `destino`) e mesmas chaves de métricas. Os
templates são os derivados da planilha do cliente (`templates/rfip/`),
produzidos por `python -m app.scripts.build_rfip_templates` a partir do
`layout.json` (ADR-13/DEC-25).

Convenções:

- WeasyPrint importado de forma preguiçosa dentro de `gerar_pdf` (GTK/Pango só
  existem no container); nada é importado de `rfo_pipeline`.
- Jinja2 e docxtpl com autoescape (`&`, `<`, `>` digitados pelo engenheiro não
  corrompem HTML nem o XML do DOCX).
- O módulo não acessa o MinIO: o chamador entrega `fotos_bytes` por
  `storage_key`. Foto referenciada e ausente levanta `KeyError`.
- Campo escalar vazio sai como '—' (DEC-33).
- Numeração de páginas (DEC-36 B): começa em 1 e é feita pelo próprio formato
  (`counter(page)` no CSS, campo `PAGE` no DOCX); não há `numero_pagina` no
  contexto.
- Quadro-resumo (DEC-36 C): opcional, controlado por `incluir_resumo`.

Contrato do contexto: ver `00_docs/backlog-auto/rfip-pipeline.md`.
"""
from __future__ import annotations

import base64
import copy
import io
import json
import time
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image

from app.services.report_generator.ltip_pipeline import (
    VAZIO,
    _chave_ordem,
    _logo_data_uri,
    _mime,
    _normalizar_ocorrencia,
    _storage_key_da_foto,
    agrupar_por_sistema,
)
from app.services.report_generator.vistoria_cautelar_pipeline import CAMPOS_RESPONSAVEL, _ou_traco

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
RFIP_TEMPLATES_DIR = TEMPLATES_DIR / "rfip"
HTML_TEMPLATE_NAME = "rfip/rfip_template.html.j2"
DOCX_TEMPLATE_NAME = "rfip/rfip_template.docx"
LAYOUT_PATH = RFIP_TEMPLATES_DIR / "layout.json"

# Caixa da foto da ficha (cm, já com a escala de impressão): é a mesma que o
# `.html.j2` usa (13,78 x 7,29). Lida do `layout.json` quando existe.
_FOTO_PADRAO_CM = (13.78, 7.29)

__all__ = ["VAZIO", "gerar_docx", "gerar_pdf", "normalizar_contexto", "renderizar_html"]


def _caixa_foto_mm() -> tuple[float, float]:
    """(largura, altura) máximas da foto na ficha, em mm."""
    largura, altura = _FOTO_PADRAO_CM
    try:
        layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
        escala = float(layout["grade"]["escala_impressao"])
        foto = layout["ficha"]["foto"]
        largura, altura = foto["largura_cm"] * escala, foto["altura_cm"] * escala
    except (OSError, KeyError, TypeError, ValueError):
        pass
    return largura * 10, altura * 10


def _data_uri(conteudo: bytes) -> str:
    return f"data:{_mime(conteudo)};base64,{base64.b64encode(conteudo).decode('ascii')}"


def _bytes_da_foto(ocorrencia: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes | None:
    storage_key = _storage_key_da_foto(ocorrencia)
    if storage_key is None:
        return None
    if storage_key not in fotos_bytes:
        raise KeyError(f"Foto '{storage_key}' da ocorrência nº {ocorrencia.get('seq_numero')} não foi fornecida.")
    return fotos_bytes[storage_key]


def normalizar_contexto(contexto: dict[str, Any]) -> dict[str, Any]:
    """Completa o contexto com o que o template do RFIP espera.

    Aceita as ocorrências já agrupadas em `sistemas` ou planas em `ocorrencias`
    (cada uma com `sistema`, RN-11). Nunca muta o `contexto` recebido. Campos
    escalares vazios viram '—' (DEC-33); `incluir_resumo` vira booleano
    (padrão: falso).
    """
    ctx = copy.deepcopy(contexto)

    responsavel = ctx.setdefault("responsavel", {})
    for chave in CAMPOS_RESPONSAVEL:
        responsavel[chave] = _ou_traco(responsavel.get(chave))
    ctx.setdefault("logo_data_uri", _logo_data_uri())
    ctx["incluir_resumo"] = bool(ctx.get("incluir_resumo"))

    if "sistemas" not in ctx:
        ctx["sistemas"] = agrupar_por_sistema(ctx.get("ocorrencias", []))
    for sistema in ctx["sistemas"]:
        sistema["nome"] = _ou_traco(sistema.get("nome"))
        sistema["ocorrencias"].sort(key=_chave_ordem)
        for ocorrencia in sistema["ocorrencias"]:
            _normalizar_ocorrencia(ocorrencia)
    return ctx


def renderizar_html(contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> str:
    """Renderiza o `.html.j2` do RFIP com as fotos embutidas como data URI."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template(HTML_TEMPLATE_NAME)
    ctx = normalizar_contexto(contexto)
    for sistema in ctx["sistemas"]:
        for ocorrencia in sistema["ocorrencias"]:
            conteudo = _bytes_da_foto(ocorrencia, fotos_bytes)
            if conteudo is not None:
                ocorrencia["foto_data_uri"] = _data_uri(conteudo)
    return template.render(**ctx)


def gerar_pdf(contexto: dict[str, Any], fotos_bytes: dict[str, bytes], destino: Path) -> dict[str, float]:
    """Renderiza o HTML (Jinja2) e converte para PDF (WeasyPrint).

    Retorna o tempo (segundos) de `render_html`, `conversao_pdf` e `total`,
    além de `n_paginas` e `tamanho_bytes` — as mesmas chaves dos outros pipelines.
    """
    from weasyprint import HTML  # preguiçoso: GTK/Pango só existem no container

    inicio_render = time.perf_counter()
    html_renderizado = renderizar_html(contexto, fotos_bytes)
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


def _inline_image(tpl: Any, conteudo: bytes, caixa_mm: tuple[float, float]) -> Any:
    """`InlineImage` que cabe na caixa da foto da ficha sem deformar a imagem."""
    from docx.shared import Mm
    from docxtpl import InlineImage

    largura_max, altura_max = caixa_mm
    with Image.open(io.BytesIO(conteudo)) as imagem:
        largura_px, altura_px = imagem.size
    if largura_px <= 0 or altura_px <= 0:
        return InlineImage(tpl, io.BytesIO(conteudo), width=Mm(largura_max))
    escala = min(largura_max / largura_px, altura_max / altura_px)
    return InlineImage(
        tpl,
        io.BytesIO(conteudo),
        width=Mm(largura_px * escala),
        height=Mm(altura_px * escala),
    )


def gerar_docx(
    contexto: dict[str, Any],
    fotos_bytes: dict[str, bytes],
    destino: Path,
    *,
    template_path: Path | None = None,
) -> dict[str, float]:
    """Renderiza o DOCX (docxtpl) a partir do template do RFIP.

    Cada ocorrência recebe `foto_docx` (`InlineImage` que cabe na caixa da
    ficha; string vazia quando não há foto). A numeração de páginas é o campo
    `PAGE` do rodapé do template.

    Retorna o tempo (segundos) de `montagem_fotos`, `render_e_salvar` e
    `total`, além de `tamanho_bytes`.
    """
    from docxtpl import DocxTemplate

    tpl = DocxTemplate(str(template_path or TEMPLATES_DIR / DOCX_TEMPLATE_NAME))
    ctx = normalizar_contexto(contexto)
    caixa_mm = _caixa_foto_mm()

    inicio_fotos = time.perf_counter()
    for sistema in ctx["sistemas"]:
        for ocorrencia in sistema["ocorrencias"]:
            conteudo = _bytes_da_foto(ocorrencia, fotos_bytes)
            ocorrencia["foto_docx"] = _inline_image(tpl, conteudo, caixa_mm) if conteudo else ""
    fim_fotos = time.perf_counter()

    tpl.render(ctx, autoescape=True)
    tpl.save(str(destino))
    fim_render = time.perf_counter()

    return {
        "montagem_fotos": fim_fotos - inicio_fotos,
        "render_e_salvar": fim_render - fim_fotos,
        "total": fim_render - inicio_fotos,
        "tamanho_bytes": destino.stat().st_size,
    }
