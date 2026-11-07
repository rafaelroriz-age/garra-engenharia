"""Pipeline de geração do Laudo de Vistoria de Imóvel Residencial (DEC-35).

Irmão de `ltip_pipeline`: mesma API (`renderizar_html`, `gerar_pdf`, `gerar_docx`,
com `contexto` + `fotos_bytes` indexado por `storage_key` + `destino`) e mesmas
chaves de métricas de retorno. Os templates consumidos são os derivados do PDF
original do cliente (`templates/vistoria_residencial/`), produzidos por
`python -m app.scripts.build_vistoria_residencial_templates` a partir de
`layout.json` — ADR-13/DEC-25.

Convenções herdadas do LTIP:

- WeasyPrint importado de forma preguiçosa, dentro de `gerar_pdf` (GTK/Pango só
  existem no container); o HTML e o DOCX são testáveis em qualquer máquina.
- Nada é importado de `rfo_pipeline`/`ltip_pipeline`: os auxiliares comuns estão
  duplicados de forma mínima (extração para módulo comum: sugestão no doc).
- Jinja2 e docxtpl com `autoescape=True`.
- O módulo não acessa o MinIO: o chamador entrega `fotos_bytes` por `storage_key`.
  Foto referenciada e ausente em `fotos_bytes` levanta `KeyError`.
- Campo vazio vira '—' (DEC-33).

Diferença em relação ao LTIP: o relatório fotográfico (cap. 8) é uma lista plana
`fotos`, e a análise (cap. 9) é por `sistemas` com `constatacoes` e
`fundamentacao_tecnica`; os textos fixos vêm em `textos.<chave>`.
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

from app.services.report_generator.foto_fetcher import RegistroDeFotos, criar_url_fetcher
from app.services.report_generator.legenda_foto import legenda_para_relatorio

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
HTML_TEMPLATE_NAME = "vistoria_residencial/vistoria_residencial_template.html.j2"
DOCX_TEMPLATE_NAME = "vistoria_residencial/vistoria_residencial_template.docx"
LOGO_SVG_PATH = TEMPLATES_DIR / "assets" / "logo-garra.svg"

# Chaves de `textos.<chave>` consumidas pelos templates (`chave_secao("4.2.1.")`
# -> `s4_2_1`), na ordem do laudo.
TEXTOS_CHAVES = (
    "s1", "s1_1",
    "s2", "s2_1", "s2_2",
    "s3", "s3_1", "s3_2",
    "s4", "s4_1", "s4_2", "s4_2_1", "s4_2_2", "s4_2_3", "s4_2_4", "s4_2_4_1", "s4_2_4_2",
    "s5", "s5_1", "s5_2",
    "s6", "s6_1", "s6_2", "s6_3",
    "s7", "s7_1",
    "s8",
    "s9",
    "s10",
    "s11",
    "s12",
)  # fmt: skip

VAZIO = "—"
# Largura útil da página A4 (21 cm - 3,00 - 1,99 de margem): foto do cap. 8 no DOCX.
LARGURA_FOTO_DOCX_MM = 160


def _em_paragrafos(valor: Any) -> list[str]:
    """Texto livre (um parágrafo por linha não vazia) ou lista -> lista de parágrafos."""
    if not valor:
        return []
    if isinstance(valor, str):
        valor = re.split(r"[\r\n]+", valor)
    return [str(item).strip() for item in valor if item is not None and str(item).strip()]


def _logo_data_uri() -> str | None:
    if not LOGO_SVG_PATH.is_file():
        return None
    return "data:image/svg+xml;base64," + base64.b64encode(LOGO_SVG_PATH.read_bytes()).decode("ascii")


def _formatar_data(valor: Any) -> str:
    if isinstance(valor, datetime):
        valor = valor.date()
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    return str(valor)


def _mime(conteudo: bytes) -> str:
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return "image/jpeg"


def _preencher(bloco: dict[str, Any], chaves: tuple[str, ...]) -> None:
    for chave in chaves:
        if bloco.get(chave) in (None, ""):
            bloco[chave] = VAZIO


def normalizar_contexto(contexto: dict[str, Any]) -> dict[str, Any]:
    """Completa o contexto com o que os templates da Vistoria Residencial esperam.

    `textos.<chave>` aceita lista ou texto livre (um parágrafo por linha); chaves
    ausentes viram lista vazia. Nunca muta o `contexto` recebido.
    """
    c = copy.deepcopy(contexto)
    for bloco, chaves in (
        ("imovel", ("unidade",)),
        ("edificacao", ("nome",)),
        ("fiscal", ("nome", "crea", "email", "telefone")),
    ):
        c[bloco] = c.get(bloco) or {}
        _preencher(c[bloco], chaves)
    c["fiscal"]["qualificacoes"] = _em_paragrafos(c["fiscal"].get("qualificacoes"))
    c.setdefault("logo_data_uri", _logo_data_uri())
    c["data_emissao"] = _formatar_data(c.get("data_emissao") or date.today())
    if c.get("local_emissao") in (None, ""):
        c["local_emissao"] = VAZIO

    textos = c.get("textos") or {}
    c["textos"] = {chave: _em_paragrafos(textos.get(chave)) for chave in TEXTOS_CHAVES}

    c["fotos"] = c.get("fotos") or []
    for indice, foto in enumerate(c["fotos"], start=1):
        foto.setdefault("numero", indice)
        # DEC-37 DP-9 (RN-16/RN-17): só `legenda` entra; sugestão de IA nunca.
        foto["legenda"] = legenda_para_relatorio(foto)
        _preencher(foto, ("legenda",))

    c["sistemas"] = c.get("sistemas") or []
    for sistema in c["sistemas"]:
        _preencher(sistema, ("nome",))
        for chave in ("constatacoes", "fundamentacao_tecnica"):
            sistema[chave] = _em_paragrafos(sistema.get(chave)) or [VAZIO]
    return c


def _bytes_da_foto(foto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes | None:
    storage_key = foto.get("storage_key")
    if not storage_key:
        return None
    if storage_key not in fotos_bytes:
        raise KeyError(f"Foto '{storage_key}' (figura nº {foto.get('numero')}) não foi fornecida.")
    return fotos_bytes[storage_key]


def _renderizar(contexto: dict[str, Any], fotos_bytes: dict[str, bytes], registro: RegistroDeFotos | None) -> str:
    """Renderiza o `.html.j2`. Com `registro`, cada foto vira `garra-foto:<n>`
    (resolvida por `url_fetcher`, DEC-41); sem ele, data URI autocontido."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template(HTML_TEMPLATE_NAME)
    contexto_html = normalizar_contexto(contexto)
    for foto in contexto_html["fotos"]:
        conteudo = _bytes_da_foto(foto, fotos_bytes)
        if conteudo is not None:
            if registro is not None:
                foto["data_uri"] = registro.registrar(conteudo)
            else:
                b64 = base64.b64encode(conteudo).decode("ascii")
                foto["data_uri"] = f"data:{_mime(conteudo)};base64,{b64}"
    return template.render(**contexto_html)


def renderizar_html(contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> str:
    """Renderiza o `.html.j2` da Vistoria Residencial com as fotos como data URI."""
    return _renderizar(contexto, fotos_bytes, None)


def gerar_pdf(contexto: dict[str, Any], fotos_bytes: dict[str, bytes], destino: Path) -> dict[str, float]:
    """Renderiza o HTML (Jinja2) e converte para PDF (WeasyPrint).

    Retorna o tempo (segundos) de `render_html`, `conversao_pdf` e `total`,
    além de `n_paginas` e `tamanho_bytes` — as mesmas chaves de `ltip_pipeline`.
    """
    from weasyprint import HTML  # preguiçoso: GTK/Pango só existem no container

    inicio_render = time.perf_counter()
    registro = RegistroDeFotos()
    fetcher = criar_url_fetcher(registro)
    html_renderizado = _renderizar(contexto, fotos_bytes, registro if fetcher else None)
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


def gerar_docx(
    contexto: dict[str, Any],
    fotos_bytes: dict[str, bytes],
    destino: Path,
    *,
    template_path: Path | None = None,
) -> dict[str, float]:
    """Renderiza o DOCX (docxtpl) a partir do template base da Vistoria Residencial.

    Cada foto recebe `imagem` (`InlineImage`, o que o template usa em
    `{{ foto.imagem }}`); foto sem `storage_key` fica com `imagem` vazia.

    Retorna o tempo (segundos) de `montagem_fotos`, `render_e_salvar` e
    `total`, além de `tamanho_bytes`.
    """
    from docx.shared import Mm
    from docxtpl import DocxTemplate, InlineImage

    tpl = DocxTemplate(str(template_path or TEMPLATES_DIR / DOCX_TEMPLATE_NAME))
    contexto_docx = normalizar_contexto(contexto)

    inicio_fotos = time.perf_counter()
    for foto in contexto_docx["fotos"]:
        conteudo = _bytes_da_foto(foto, fotos_bytes)
        foto["imagem"] = InlineImage(tpl, io.BytesIO(conteudo), width=Mm(LARGURA_FOTO_DOCX_MM)) if conteudo else ""
    fim_fotos = time.perf_counter()

    tpl.render(contexto_docx, autoescape=True)
    tpl.save(str(destino))
    fim_render = time.perf_counter()

    return {
        "montagem_fotos": fim_fotos - inicio_fotos,
        "render_e_salvar": fim_render - fim_fotos,
        "total": fim_render - inicio_fotos,
        "tamanho_bytes": destino.stat().st_size,
    }
