"""Pipeline de geração do Laudo Técnico de Inspeção Predial — LTIP (BL-17).

Irmão de `rfo_pipeline`: mesma API (`normalizar_contexto`, `gerar_pdf`,
`gerar_docx`, com `contexto` + `fotos_bytes` indexado por `storage_key` +
`destino`) e mesmas métricas de retorno. Os templates consumidos são os
derivados do PDF original do cliente (`templates/ltip/`), produzidos por
`python -m app.scripts.build_ltip_templates` a partir de
`templates/ltip/layout.json` — ADR-13/DEC-25.

Diferenças em relação ao RFO:

- O WeasyPrint é importado de forma preguiçosa, dentro de `gerar_pdf`: ele só
  carrega no container (GTK/Pango ausentes no Windows), e o contexto, o HTML e o
  DOCX precisam ser testáveis em qualquer máquina.
- Por isso nada é importado de `rfo_pipeline` (que importa `weasyprint` no topo
  do módulo); os dois auxiliares comuns estão duplicados aqui de forma mínima.
  A extração para um módulo comum está registrada como sugestão em
  `00_docs/backlog-auto/ltip-pipeline.md`.
- O DOCX é renderizado com `autoescape=True`, para que `&`, `<` e `>` digitados
  pelo engenheiro não corrompam o XML do documento.

Assim como no RFO, o módulo não acessa o storage (MinIO): o chamador baixa as
fotos e entrega os bytes; o redimensionamento prévio é responsabilidade dele.
"""
from __future__ import annotations

import base64
import copy
import io
import re
import time
from collections import OrderedDict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
LTIP_TEMPLATES_DIR = TEMPLATES_DIR / "ltip"
HTML_TEMPLATE_NAME = "ltip/ltip_template.html.j2"
DOCX_TEMPLATE_NAME = "ltip/ltip_template.docx"
# Marca vetorizada com fundo transparente (RN-07/B-02). O DOCX não aceita SVG e
# já traz o PNG equivalente embutido no próprio template.
LOGO_SVG_PATH = TEMPLATES_DIR / "assets" / "logo-garra.svg"

# Seções de texto corrido do template (`{% for paragrafo in <chave>_paragrafos %}`),
# na mesma ordem de `build_ltip_templates.SECOES_CORPO` + conclusão.
SECOES_TEXTO = (
    "introducao",
    "consideracoes_preliminares",
    "objetivo",
    "objeto",
    "metodologia",
    "documentacao_analisada",
    "conclusao",
)

# Campos da ficha fotográfica que o template imprime sem fallback no DOCX.
CAMPOS_FICHA = (
    "situacao",
    "prioridade",
    "gut_gravidade",
    "gut_urgencia",
    "gut_tendencia",
    "pontuacao_gut",
    "classificacao",
    "grau_risco",
    "subsistema",
    "localizacao",
    "descricao",
)
VAZIO = "—"
# Largura da foto na ficha do DOCX: metade útil da página A4 (2 fichas por linha).
LARGURA_FOTO_DOCX_MM = 80

_ORDEM_INDEFINIDA = 10**9
# Esquema das fotos servidas da memória ao WeasyPrint em `gerar_pdf` (T20).
ESQUEMA_FOTO = "garra-foto:"


def _em_paragrafos(texto: str | None) -> list[str]:
    """Quebra um campo de texto livre em parágrafos (um por linha não vazia)."""
    if not texto:
        return []
    return [item.strip() for item in re.split(r"[\r\n]+", texto) if item.strip()]


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


def _numero(valor: Any) -> Any:
    """`3.0` -> `3`: as notas GUT são `Float` no modelo, mas inteiras na prática."""
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return valor


def _pontuacao_gut(ocorrencia: dict[str, Any]) -> Any:
    """Pontuação GUT = Gravidade x Urgência x Tendência, quando as três existem."""
    notas = [ocorrencia.get(chave) for chave in ("gut_gravidade", "gut_urgencia", "gut_tendencia")]
    if any(nota is None for nota in notas):
        return None
    return _numero(notas[0] * notas[1] * notas[2])


def _mime(conteudo: bytes) -> str:
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return "image/jpeg"


def _storage_key_da_foto(ocorrencia: dict[str, Any]) -> str | None:
    """A ficha do LTIP mostra uma foto por ocorrência: a primeira de `fotos`."""
    fotos = ocorrencia.get("fotos") or []
    if not fotos:
        return None
    return fotos[0]["storage_key"]


def _normalizar_ocorrencia(ocorrencia: dict[str, Any]) -> None:
    for chave in ("gut_gravidade", "gut_urgencia", "gut_tendencia"):
        ocorrencia[chave] = _numero(ocorrencia.get(chave))
    if ocorrencia.get("pontuacao_gut") is None:
        ocorrencia["pontuacao_gut"] = _pontuacao_gut(ocorrencia)
    # `TIPO` é `tipo_anomalia or tipo_falha`: só o último elo recebe o traço.
    if not ocorrencia.get("tipo_anomalia") and not ocorrencia.get("tipo_falha"):
        ocorrencia["tipo_falha"] = VAZIO
    for chave in CAMPOS_FICHA:
        if ocorrencia.get(chave) in (None, ""):
            ocorrencia[chave] = VAZIO


def _chave_ordem(ocorrencia: dict[str, Any]) -> tuple[int, str, int]:
    """RN-11: dentro do sistema, por Subsistema (ordem do gabarito) e depois nº da foto."""
    ordem = ocorrencia.get("subsistema_ordem")
    return (
        _ORDEM_INDEFINIDA if ordem is None else ordem,
        str(ocorrencia.get("subsistema") or ""),
        ocorrencia.get("seq_numero") or 0,
    )


def agrupar_por_sistema(ocorrencias: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa ocorrências planas em `[{"nome", "ordem", "ocorrencias"}]` (RN-11).

    Cada ocorrência informa `sistema` (nome) e, opcionalmente, `sistema_ordem` e
    `subsistema_ordem` — as colunas `ordem` do gabarito (`SistemaPredial`,
    `Subsistema`). Sem ordem, vale a ordem de primeira aparição.
    """
    grupos: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for ocorrencia in ocorrencias:
        nome = ocorrencia.get("sistema")
        if not nome:
            raise ValueError(f"Ocorrência nº {ocorrencia.get('seq_numero')} sem sistema predial (RN-11).")
        grupo = grupos.setdefault(nome, {"nome": nome, "ordem": ocorrencia.get("sistema_ordem"), "ocorrencias": []})
        grupo["ocorrencias"].append(ocorrencia)
    sistemas = list(grupos.values())
    posicao = {grupo["nome"]: indice for indice, grupo in enumerate(sistemas)}
    sistemas.sort(key=lambda g: (_ORDEM_INDEFINIDA if g["ordem"] is None else g["ordem"], posicao[g["nome"]]))
    return sistemas


def normalizar_contexto(contexto: dict[str, Any]) -> dict[str, Any]:
    """Completa o contexto com o que o template derivado do LTIP espera.

    Aceita as seções de texto como `<chave>_paragrafos` (lista) ou `<chave>`
    (texto livre, um parágrafo por linha) e as ocorrências já agrupadas em
    `sistemas` ou planas em `ocorrencias`. Nunca muta o `contexto` recebido.
    """
    normalizado = copy.deepcopy(contexto)
    normalizado.setdefault("edificacao", {})
    normalizado.setdefault("fiscal", {})
    normalizado.setdefault("contrato", {})
    normalizado.setdefault("logo_data_uri", _logo_data_uri())
    normalizado["data_emissao"] = _formatar_data(normalizado.get("data_emissao") or date.today())
    for chave in SECOES_TEXTO:
        normalizado.setdefault(f"{chave}_paragrafos", _em_paragrafos(normalizado.get(chave)))

    if "sistemas" not in normalizado:
        normalizado["sistemas"] = agrupar_por_sistema(normalizado.get("ocorrencias", []))
    for sistema in normalizado["sistemas"]:
        sistema["ocorrencias"].sort(key=_chave_ordem)
        for ocorrencia in sistema["ocorrencias"]:
            _normalizar_ocorrencia(ocorrencia)
    return normalizado


def _bytes_da_foto(ocorrencia: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes | None:
    storage_key = _storage_key_da_foto(ocorrencia)
    if storage_key is None:
        return None
    if storage_key not in fotos_bytes:
        raise KeyError(f"Foto '{storage_key}' da ocorrência nº {ocorrencia.get('seq_numero')} não foi fornecida.")
    return fotos_bytes[storage_key]


def _renderizar(contexto: dict[str, Any], fotos_bytes: dict[str, bytes], fotos_em_memoria: list[bytes] | None) -> str:
    """Renderiza o `.html.j2`; cada ficha recebe `foto_src`.

    Com `fotos_em_memoria=None`, `foto_src` é um data URI (HTML autocontido).
    Com uma lista, a foto é anexada a ela e `foto_src` vira `garra-foto:<índice>`,
    resolvido por `_FetcherDeFotos` sem passar por base64 (ver `gerar_pdf`).
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template(HTML_TEMPLATE_NAME)
    contexto_html = normalizar_contexto(contexto)
    for sistema in contexto_html["sistemas"]:
        for ocorrencia in sistema["ocorrencias"]:
            conteudo = _bytes_da_foto(ocorrencia, fotos_bytes)
            if conteudo is None:
                continue
            if fotos_em_memoria is None:
                b64 = base64.b64encode(conteudo).decode("ascii")
                ocorrencia["foto_src"] = f"data:{_mime(conteudo)};base64,{b64}"
            else:
                ocorrencia["foto_src"] = f"{ESQUEMA_FOTO}{len(fotos_em_memoria)}"
                fotos_em_memoria.append(conteudo)
    return template.render(**contexto_html)


def renderizar_html(contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> str:
    """Renderiza o `.html.j2` do LTIP com as fotos embutidas como data URI."""
    return _renderizar(contexto, fotos_bytes, None)


def _fetcher_de_fotos(fotos_em_memoria: list[bytes]) -> Any | None:
    """`url_fetcher` do WeasyPrint que entrega as fotos direto da memória.

    Evita o base64 de ~28 MB no HTML (239 fotos): o parse do HTML cai de ~2,3 s
    para ~0,3 s e o pico de RSS, de ~380 MB para ~290 MB (T20). Outras URLs
    (o logo em data URI) seguem para o fetcher padrão. Em WeasyPrint sem a
    classe `URLFetcher` (API anterior), devolve `None` e o chamador volta aos
    data URIs.
    """
    try:
        from weasyprint.urls import URLFetcher, URLFetcherResponse
    except ImportError:  # pragma: no cover - depende da versão instalada no container
        return None

    class _FetcherDeFotos(URLFetcher):
        def fetch(self, url: str, headers: Any = None) -> Any:
            if url.startswith(ESQUEMA_FOTO):
                conteudo = fotos_em_memoria[int(url[len(ESQUEMA_FOTO):])]
                return URLFetcherResponse(url, conteudo, {"Content-Type": _mime(conteudo)})
            return super().fetch(url, headers)

    return _FetcherDeFotos()


def gerar_pdf(contexto: dict[str, Any], fotos_bytes: dict[str, bytes], destino: Path) -> dict[str, float]:
    """Renderiza o HTML (Jinja2) e converte para PDF (WeasyPrint).

    Retorna o tempo (segundos) de `render_html`, `conversao_pdf` e `total`,
    além de `n_paginas` e `tamanho_bytes` — as mesmas chaves de `rfo_pipeline`.
    """
    from weasyprint import HTML  # preguiçoso: GTK/Pango só existem no container

    inicio_render = time.perf_counter()
    fotos_em_memoria: list[bytes] = []
    fetcher = _fetcher_de_fotos(fotos_em_memoria)
    html_renderizado = _renderizar(contexto, fotos_bytes, fotos_em_memoria if fetcher else None)
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
    """Renderiza o DOCX (docxtpl) a partir do template base do LTIP.

    Cada ocorrência recebe `foto` (`InlineImage`, criado sem custo de render).
    O template versionado ainda não tem o placeholder `{{ ocorrencia.foto }}`
    na ficha (lacuna de BL-17 registrada no doc da tarefa); assim que o gerador
    do template o incluir, a foto passa a sair no DOCX sem mudar este módulo.

    Retorna o tempo (segundos) de `montagem_fotos`, `render_e_salvar` e
    `total`, além de `tamanho_bytes`.
    """
    from docx.shared import Mm
    from docxtpl import DocxTemplate, InlineImage

    tpl = DocxTemplate(str(template_path or TEMPLATES_DIR / DOCX_TEMPLATE_NAME))
    contexto_docx = normalizar_contexto(contexto)

    inicio_fotos = time.perf_counter()
    for sistema in contexto_docx["sistemas"]:
        for ocorrencia in sistema["ocorrencias"]:
            conteudo = _bytes_da_foto(ocorrencia, fotos_bytes)
            ocorrencia["foto"] = (
                InlineImage(tpl, io.BytesIO(conteudo), width=Mm(LARGURA_FOTO_DOCX_MM)) if conteudo else ""
            )
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
