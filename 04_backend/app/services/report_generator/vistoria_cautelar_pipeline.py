"""Pipeline de geração da Vistoria Cautelar de Recebimento de Obra (DEC-35).

Irmão de `ltip_pipeline`: mesma API (`renderizar_html`, `gerar_pdf`,
`gerar_docx`, com `contexto` + `fotos_bytes` indexado por `storage_key` +
`destino`) e mesmas chaves de métricas. Os templates são os derivados do PDF
original do cliente (`templates/vistoria_cautelar/`), produzidos por
`python -m app.scripts.build_vistoria_cautelar_templates` a partir do
`layout.json` — ADR-13/DEC-25.

Convenções (iguais às do LTIP):

- WeasyPrint importado de forma preguiçosa dentro de `gerar_pdf` (GTK/Pango só
  existem no container); nada é importado de `rfo_pipeline`.
- Jinja2 e docxtpl com autoescape (`&`, `<`, `>` digitados pelo engenheiro não
  corrompem HTML nem o XML do DOCX).
- O módulo não acessa o MinIO: o chamador entrega `fotos_bytes` por
  `storage_key`. Foto referenciada e ausente levanta `KeyError`.
- Campo escalar vazio sai como '—' (DEC-33).

Contrato do contexto: ver `00_docs/backlog-auto/vistoria-cautelar-pipeline.md`.
"""
from __future__ import annotations

import base64
import copy
import io
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
VISTORIA_TEMPLATES_DIR = TEMPLATES_DIR / "vistoria_cautelar"
HTML_TEMPLATE_NAME = "vistoria_cautelar/vistoria_cautelar_template.html.j2"
DOCX_TEMPLATE_NAME = "vistoria_cautelar/vistoria_cautelar_template.docx"
LOGO_SVG_PATH = TEMPLATES_DIR / "assets" / "logo-garra.svg"

VAZIO = "—"
# Largura útil da página A4 do layout: 21 cm - 3,0 - 2,03 = ~16 cm.
LARGURA_FIGURA_DOCX_MM = 140
LARGURA_ASSINATURA_DOCX_MM = 40

CAMPOS_RESPONSAVEL = ("nome", "titulo_profissional", "crea", "email", "telefone")
CHAVES_TABELAS = {
    "identificacao": ("aspecto_tecnico", "descricao_detalhada"),
    "plano_de_correcoes_remanescentes": (
        "item",
        "localizacao",
        "descricao_da_pendencia",
        "metodologia_corretiva_indicada",
    ),
}

_MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)  # fmt: skip


def _vazio(valor: Any) -> bool:
    return valor is None or (isinstance(valor, str) and not valor.strip())


def _ou_traco(valor: Any) -> Any:
    return VAZIO if _vazio(valor) else valor


def _em_paragrafos(valor: Any) -> list[str]:
    """Lista de parágrafos; texto livre vira um parágrafo por linha não vazia."""
    if _vazio(valor):
        return []
    if isinstance(valor, str):
        return [item.strip() for item in re.split(r"[\r\n]+", valor) if item.strip()]
    return [str(item) for item in valor if not _vazio(item)]


def _como_data(valor: Any) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        return date.fromisoformat(valor[:10])
    return date.today()


def _logo_data_uri() -> str | None:
    if not LOGO_SVG_PATH.is_file():
        return None
    return "data:image/svg+xml;base64," + base64.b64encode(LOGO_SVG_PATH.read_bytes()).decode("ascii")


def _mime(conteudo: bytes) -> str:
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return "image/jpeg"


def _data_uri(conteudo: bytes) -> str:
    return f"data:{_mime(conteudo)};base64,{base64.b64encode(conteudo).decode('ascii')}"


def _bytes_da_foto(storage_key: str | None, fotos_bytes: dict[str, bytes], onde: str) -> bytes | None:
    if not storage_key:
        return None
    if storage_key not in fotos_bytes:
        raise KeyError(f"Foto '{storage_key}' ({onde}) não foi fornecida.")
    return fotos_bytes[storage_key]


def normalizar_contexto(contexto: dict[str, Any]) -> dict[str, Any]:
    """Completa o contexto com o que o template da Vistoria Cautelar espera.

    Nunca muta o `contexto` recebido. Campos escalares vazios viram '—'
    (DEC-33); listas de parágrafos aceitam texto livre (um parágrafo por linha).
    """
    ctx = copy.deepcopy(contexto)

    responsavel = ctx.setdefault("responsavel", {})
    for chave in CAMPOS_RESPONSAVEL:
        responsavel[chave] = _ou_traco(responsavel.get(chave))
    responsavel["qualificacoes"] = _em_paragrafos(responsavel.get("qualificacoes"))

    obra = ctx.setdefault("obra", {})
    obra["descricao"] = _ou_traco(obra.get("descricao"))
    edificacao = ctx.setdefault("edificacao", {})
    edificacao["nome"] = _ou_traco(edificacao.get("nome"))

    emissao = _como_data(ctx.get("data_emissao"))
    ctx["data_emissao_mes_ano"] = _ou_traco(
        ctx.get("data_emissao_mes_ano") or f"{_MESES[emissao.month - 1].capitalize()} de {emissao.year}"
    )
    ctx["data_emissao_extenso"] = _ou_traco(
        ctx.get("data_emissao_extenso") or f"{emissao.day} de {_MESES[emissao.month - 1]} de {emissao.year}"
    )
    ctx["local_emissao"] = _ou_traco(ctx.get("local_emissao"))
    ctx.setdefault("logo_data_uri", _logo_data_uri())

    ctx["conteudo"] = {chave: _em_paragrafos(valor) for chave, valor in (ctx.get("conteudo") or {}).items()}
    ctx["complementos"] = dict(ctx.get("complementos") or {})

    tabelas = {}
    for nome, colunas in CHAVES_TABELAS.items():
        linhas = (ctx.get("tabelas") or {}).get(nome) or []
        tabelas[nome] = [{coluna: _ou_traco(linha.get(coluna)) for coluna in colunas} for linha in linhas]
    ctx["tabelas"] = tabelas

    sistemas = ctx.get("sistemas") or []
    for sistema in sistemas:
        sistema["nome"] = _ou_traco(sistema.get("nome"))
        sistema["constatacoes"] = _em_paragrafos(sistema.get("constatacoes"))
        sistema["fundamentacao_tecnica"] = _em_paragrafos(sistema.get("fundamentacao_tecnica"))
    ctx["sistemas"] = sistemas

    figuras = ctx.get("figuras") or []
    for indice, figura in enumerate(figuras, start=1):
        figura["numero"] = figura.get("numero") or indice
        figura["legenda"] = _ou_traco(figura.get("legenda"))
    ctx["figuras"] = figuras
    return ctx


def renderizar_html(contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> str:
    """Renderiza o `.html.j2` com as imagens embutidas como data URI."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template(HTML_TEMPLATE_NAME)
    ctx = normalizar_contexto(contexto)

    for figura in ctx["figuras"]:
        conteudo = _bytes_da_foto(figura.get("storage_key"), fotos_bytes, f"figura {figura['numero']}")
        if conteudo is not None:
            figura["foto_data_uri"] = _data_uri(conteudo)
    for chave_storage, chave_uri in (
        ("assinatura_storage_key", "assinatura_data_uri"),
        ("capa_fundo_storage_key", "capa_fundo_data_uri"),
    ):
        conteudo = _bytes_da_foto(ctx.get(chave_storage), fotos_bytes, chave_storage)
        if conteudo is not None:
            ctx[chave_uri] = _data_uri(conteudo)
    return template.render(**ctx)


def gerar_pdf(contexto: dict[str, Any], fotos_bytes: dict[str, bytes], destino: Path) -> dict[str, float]:
    """Renderiza o HTML (Jinja2) e converte para PDF (WeasyPrint).

    Retorna `render_html`, `conversao_pdf` e `total` (segundos), além de
    `n_paginas` e `tamanho_bytes` — as mesmas chaves de `ltip_pipeline`.
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


def gerar_docx(
    contexto: dict[str, Any],
    fotos_bytes: dict[str, bytes],
    destino: Path,
    *,
    template_path: Path | None = None,
) -> dict[str, float]:
    """Renderiza o DOCX (docxtpl) a partir do template da Vistoria Cautelar.

    Cada figura recebe `imagem` e o contexto recebe `assinatura_imagem`
    (`InlineImage`; string vazia quando não há foto). A arte de fundo da capa
    só existe no HTML.

    Retorna `montagem_fotos`, `render_e_salvar` e `total` (segundos), além de
    `tamanho_bytes`.
    """
    from docx.shared import Mm
    from docxtpl import DocxTemplate, InlineImage

    tpl = DocxTemplate(str(template_path or TEMPLATES_DIR / DOCX_TEMPLATE_NAME))
    ctx = normalizar_contexto(contexto)

    inicio_fotos = time.perf_counter()
    for figura in ctx["figuras"]:
        conteudo = _bytes_da_foto(figura.get("storage_key"), fotos_bytes, f"figura {figura['numero']}")
        figura["imagem"] = (
            InlineImage(tpl, io.BytesIO(conteudo), width=Mm(LARGURA_FIGURA_DOCX_MM)) if conteudo else ""
        )
    assinatura = _bytes_da_foto(ctx.get("assinatura_storage_key"), fotos_bytes, "assinatura_storage_key")
    ctx["assinatura_imagem"] = (
        InlineImage(tpl, io.BytesIO(assinatura), width=Mm(LARGURA_ASSINATURA_DOCX_MM)) if assinatura else ""
    )
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
