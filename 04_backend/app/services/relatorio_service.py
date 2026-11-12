"""Emissão de relatórios (PDF + DOCX) a partir do banco, por tipo (BL-13, V1-02, RF-06, RN-18/DEC-27).

Cada tipo de relatório é um `Emissor` registrado em `EMISSORES` (hoje RFO e
VISTORIA_CAUTELAR): ele sabe montar e validar o contexto, quais fotos o template embute e
qual módulo de `app.services.report_generator` renderiza o documento. Contrato
e passo a passo para registrar um tipo novo: 00_docs/backlog-auto/v1-emissao-generica.md.

Fluxo (`emitir_relatorio`): tipo registrado (422) → inspeção existe (404) e é
do tipo pedido (409) → `montar_contexto` → `validar_contexto` (422) → baixa as
fotos do storage → renderiza PDF e DOCX (renderizador injetável) → trava a
inspeção → calcula a próxima versão do tipo → grava os arquivos em chaves
determinísticas → cria um `Relatorio` novo por emissão (versões anteriores
preservadas).

O `Renderizador` importa o pipeline (WeasyPrint) sob demanda: sem as
bibliotecas nativas (GTK/Pango, ex.: Windows fora do container) a emissão falha
com 503 `gerador-relatorio-indisponivel`, nunca com 500.
"""
from __future__ import annotations

import asyncio
import logging
import re
import tempfile
import uuid
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, DomainError, NotFoundError
from app.models import Inspecao, Relatorio
from app.schemas.portal import PortalDownloadRead
from app.services import portal_service
from app.services.report_generator.imagem import otimizar_imagem
from app.services.report_generator.ltip_contexto import (
    TIPO_LTIP,
    extrair_fotos_ltip,
    montar_contexto_ltip,
    validar_contexto_ltip,
)
from app.services.report_generator.rfip_contexto import (
    TIPO_RFIP,
    extrair_fotos_rfip,
    montar_contexto_rfip,
    validar_contexto_rfip,
)
from app.services.report_generator.rfo_contexto import (
    TIPO_RFO,
    montar_contexto_rfo,
    validar_contexto_rfo,
)
from app.services.report_generator.vistoria_cautelar_contexto import (
    TIPO_VISTORIA_CAUTELAR,
    extrair_fotos_vistoria_cautelar,
    montar_contexto_vistoria_cautelar,
    validar_contexto_vistoria_cautelar,
)
from app.services.report_generator.vistoria_residencial_contexto import (
    TIPO_VISTORIA_RESIDENCIAL,
    anexar_imagens_do_storage,
    extrair_fotos_vistoria_residencial,
    montar_contexto_vistoria_residencial,
    validar_contexto_vistoria_residencial,
)
from app.services.storage import ObjectNotFoundError, StorageClient

logger = logging.getLogger(__name__)

STATUS_EMITIDO = "emitido"
CONTENT_TYPE_PDF = "application/pdf"
CONTENT_TYPE_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
# Um relatório com muitas fotos passa fácil do limite de foto de `StorageClient.upload`.
MAX_RELATORIO_SIZE_BYTES = 200 * 1024 * 1024
_VERSAO_RE = re.compile(r"^V(\d+)$")
PACOTE_PIPELINES = "app.services.report_generator"


# --- erros -------------------------------------------------------------------------


class ContextoIncompletoError(DomainError):
    """Contexto sem campos que o template imprime sem fallback (DEC-47). Vira HTTP 422.

    `type_suffix` = `{tipo}-contexto-incompleto` (ex.: `rfo-contexto-incompleto`).
    """

    def __init__(self, tipo: str, campos_faltantes: list[str]) -> None:
        super().__init__(
            f"Dados obrigatórios do {tipo} ausentes: " + ", ".join(campos_faltantes) + ".",
            type_suffix=f"{tipo.lower()}-contexto-incompleto",
            title=f"Contexto do {tipo} incompleto",
            status_code=422,
            errors=[
                {"field": campo, "message": f"Campo obrigatório para emitir o {tipo}."}
                for campo in campos_faltantes
            ],
        )
        self.tipo = tipo
        self.campos_faltantes = campos_faltantes


class RfoContextoIncompletoError(ContextoIncompletoError):
    """Compatibilidade (BL-13/DEC-47): `ContextoIncompletoError` do RFO."""

    def __init__(self, campos_faltantes: list[str]) -> None:
        super().__init__(TIPO_RFO, campos_faltantes)


class TipoRelatorioNaoRegistradoError(DomainError):
    """Tipo sem `Emissor` registrado. Vira HTTP 422 com a lista de tipos disponíveis."""

    def __init__(self, tipo: str, disponiveis: list[str]) -> None:
        super().__init__(
            f"Tipo de relatório '{tipo}' não é emitível. Tipos disponíveis: " + ", ".join(disponiveis) + ".",
            type_suffix="tipo-relatorio-nao-registrado",
            title="Tipo de relatório não registrado",
            status_code=422,
            errors=[{"field": "tipo", "message": "Use um dos tipos disponíveis.", "disponiveis": disponiveis}],
        )
        self.tipo = tipo
        self.disponiveis = disponiveis


class GeradorIndisponivelError(DomainError):
    """Motor de renderização sem dependências nativas. Vira HTTP 503."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            detail,
            type_suffix="gerador-relatorio-indisponivel",
            title="Gerador de relatório indisponível",
            status_code=503,
        )


# --- renderização --------------------------------------------------------------------


class RenderizadorProtocol(Protocol):
    """O que a emissão consome: bytes do PDF e do DOCX a partir do contexto e das fotos."""

    def gerar_pdf(self, contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes: ...

    def gerar_docx(self, contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes: ...


# Compatibilidade: nome usado por `app/api/v1/relatorios.py` e testes do BL-13.
RenderizadorRFO = RenderizadorProtocol


class Renderizador:
    """Adapta um pipeline (`gerar_pdf/gerar_docx(contexto, fotos, destino)`) para devolver bytes.

    `pipeline` é o nome do módulo em `app.services.report_generator` (importado
    sob demanda, para não carregar o WeasyPrint fora do container) ou o próprio
    módulo já importado. As fotos passam por `otimizar_imagem` antes de embutir.
    """

    def __init__(self, pipeline: str | ModuleType, *, otimizar_fotos: bool = True) -> None:
        self.pipeline = pipeline
        self.otimizar_fotos = otimizar_fotos

    def _pipeline(self) -> Any:
        if isinstance(self.pipeline, ModuleType):
            return self.pipeline
        try:
            pacote = __import__(PACOTE_PIPELINES, fromlist=[self.pipeline])
            return getattr(pacote, self.pipeline)
        except (ImportError, OSError) as exc:  # OSError: libpango/libgobject ausentes
            logger.warning("Pipeline '%s' indisponível: %s", self.pipeline, exc)
            raise GeradorIndisponivelError(
                "O gerador de PDF (WeasyPrint) não está disponível neste servidor: faltam as "
                "bibliotecas nativas GTK/Pango. Gere o relatório pelo container da API."
            ) from exc

    def _gerar(self, metodo: str, extensao: str, contexto: dict[str, Any], fotos: dict[str, bytes]) -> bytes:
        pipeline = self._pipeline()
        if self.otimizar_fotos:
            fotos = {chave: otimizar_imagem(conteudo) for chave, conteudo in fotos.items()}
        with tempfile.TemporaryDirectory(prefix="relatorio-") as pasta:
            destino = Path(pasta) / f"relatorio.{extensao}"
            getattr(pipeline, metodo)(contexto, fotos, destino)
            return destino.read_bytes()

    def gerar_pdf(self, contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes:
        return self._gerar("gerar_pdf", "pdf", contexto, fotos_bytes)

    def gerar_docx(self, contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes:
        return self._gerar("gerar_docx", "docx", contexto, fotos_bytes)


class RenderizadorRFOPadrao(Renderizador):
    """Compatibilidade (BL-13): `Renderizador` do `rfo_pipeline`."""

    def __init__(self) -> None:
        super().__init__("rfo_pipeline")


# --- registro de emissores --------------------------------------------------------------


@dataclass(frozen=True)
class Emissor:
    """Como emitir um tipo de relatório. Contrato em 00_docs/backlog-auto/v1-emissao-generica.md.

    - `tipo`: valor de `Inspecao.tipo`/`Relatorio.tipo` (maiúsculas, ex. `RFO`).
    - `montar_contexto(db, inspecao_id)`: dict consumido pelo pipeline. Pode lançar
      404/409; a emissão já garante antes que a inspeção existe e é deste tipo.
    - `validar_contexto(contexto)`: caminhos obrigatórios ausentes (lista vazia = ok).
    - `extrair_fotos(contexto)`: `storage_key` das fotos que o template embute.
    - `pipeline`: módulo em `app.services.report_generator` com `gerar_pdf` e `gerar_docx`.
    - `anexar_do_storage(contexto, storage)` (opcional): completa o contexto com arquivos
      opcionais do storage (ex.: assinatura e capa como data URI). Roda depois da validação;
      deve tratar os próprios erros (arquivo opcional ausente não derruba a emissão).
    """

    tipo: str
    montar_contexto: Callable[[AsyncSession, uuid.UUID], Awaitable[dict[str, Any]]]
    validar_contexto: Callable[[dict[str, Any]], list[str]]
    extrair_fotos: Callable[[dict[str, Any]], set[str]]
    pipeline: str
    anexar_do_storage: Callable[[dict[str, Any], StorageClient], None] | None = None

    def criar_renderizador(self) -> RenderizadorProtocol:
        return Renderizador(self.pipeline)


EMISSORES: dict[str, Emissor] = {}


def normalizar_tipo(tipo: str) -> str:
    return tipo.strip().upper()


def registrar_emissor(tipo: str, emissor: Emissor) -> Emissor:
    """Registra (ou substitui) o emissor de `tipo`. Devolve o próprio emissor."""
    chave = normalizar_tipo(tipo)
    if normalizar_tipo(emissor.tipo) != chave:
        raise ValueError(f"Emissor do tipo '{emissor.tipo}' registrado como '{chave}'.")
    EMISSORES[chave] = emissor
    return emissor


def tipos_disponiveis() -> list[str]:
    return sorted(EMISSORES)


def obter_emissor(tipo: str) -> Emissor:
    """Emissor de `tipo` (sem diferenciar maiúsculas) ou 422 com os tipos disponíveis."""
    emissor = EMISSORES.get(normalizar_tipo(tipo))
    if emissor is None:
        raise TipoRelatorioNaoRegistradoError(normalizar_tipo(tipo), tipos_disponiveis())
    return emissor


def storage_keys_das_fotos(contexto: dict[str, Any]) -> list[str]:
    """Fotos que o `rfo_pipeline` embute: só as das visitas (o template não imprime ocorrências)."""
    chaves = [f["storage_key"] for v in contexto.get("visitas", []) for f in v.get("fotos", [])]
    return list(dict.fromkeys(chaves))


def extrair_fotos_rfo(contexto: dict[str, Any]) -> set[str]:
    return set(storage_keys_das_fotos(contexto))


registrar_emissor(
    TIPO_RFO,
    Emissor(
        tipo=TIPO_RFO,
        montar_contexto=montar_contexto_rfo,
        validar_contexto=validar_contexto_rfo,
        extrair_fotos=extrair_fotos_rfo,
        pipeline="rfo_pipeline",
    ),
)

registrar_emissor(
    TIPO_LTIP,
    Emissor(
        tipo=TIPO_LTIP,
        montar_contexto=montar_contexto_ltip,
        validar_contexto=validar_contexto_ltip,
        extrair_fotos=extrair_fotos_ltip,
        pipeline="ltip_pipeline",
    ),
)

registrar_emissor(
    TIPO_RFIP,
    Emissor(
        tipo=TIPO_RFIP,
        montar_contexto=montar_contexto_rfip,
        validar_contexto=validar_contexto_rfip,
        extrair_fotos=extrair_fotos_rfip,
        pipeline="rfip_pipeline",
    ),
)

registrar_emissor(
    TIPO_VISTORIA_CAUTELAR,
    Emissor(
        tipo=TIPO_VISTORIA_CAUTELAR,
        montar_contexto=montar_contexto_vistoria_cautelar,
        validar_contexto=validar_contexto_vistoria_cautelar,
        extrair_fotos=extrair_fotos_vistoria_cautelar,
        pipeline="vistoria_cautelar_pipeline",
    ),
)

registrar_emissor(
    TIPO_VISTORIA_RESIDENCIAL,
    Emissor(
        tipo=TIPO_VISTORIA_RESIDENCIAL,
        montar_contexto=montar_contexto_vistoria_residencial,
        validar_contexto=validar_contexto_vistoria_residencial,
        extrair_fotos=extrair_fotos_vistoria_residencial,
        pipeline="vistoria_residencial_pipeline",
        anexar_do_storage=anexar_imagens_do_storage,
    ),
)


# --- versão, chave e storage ------------------------------------------------------------


def chave_relatorio(inspecao_id: uuid.UUID, versao: str, extensao: str, tipo: str = TIPO_RFO) -> str:
    """Chave determinística no storage: `relatorios/{inspecao_id}/{tipo}-{versao}.{ext}` em minúsculas.

    Ex.: `relatorios/{id}/rfo-v01.pdf` (formato do BL-13 preservado).
    """
    return f"relatorios/{inspecao_id}/{tipo.lower()}-{versao.lower()}.{extensao}"


def proxima_versao(versoes: list[str]) -> str:
    """`V01`, `V02`... Ignora valores fora do padrão (ex.: cargas manuais antigas)."""
    numeros = [int(m.group(1)) for v in versoes if (m := _VERSAO_RE.match(v or ""))]
    return f"V{max(numeros, default=0) + 1:02d}"


def _baixar_fotos(storage: StorageClient, chaves: Iterable[str]) -> dict[str, bytes]:
    fotos: dict[str, bytes] = {}
    for chave in sorted(chaves):
        try:
            fotos[chave] = storage.download(chave)
        except ObjectNotFoundError as exc:
            raise ConflictError(
                f"A foto '{chave}' está vinculada à inspeção mas não existe no storage.",
                type_suffix="foto-ausente-no-storage",
            ) from exc
    return fotos


def _apagar_sem_falhar(storage: StorageClient, chaves: list[str]) -> None:
    for chave in chaves:
        try:
            storage.delete(chave)
        except Exception:  # limpeza best-effort; o erro original prevalece
            logger.exception("Falha ao remover '%s' após erro na emissão do relatório", chave)


async def _exigir_inspecao_do_tipo(db: AsyncSession, inspecao_id: uuid.UUID, tipo: str) -> None:
    tipo_inspecao = (await db.execute(select(Inspecao.tipo).where(Inspecao.id == inspecao_id))).scalar_one_or_none()
    if tipo_inspecao is None:
        raise NotFoundError(f"Inspeção '{inspecao_id}' não encontrada.", type_suffix="inspecao-nao-encontrada")
    if tipo_inspecao != tipo:
        raise ConflictError(
            f"Inspeção '{inspecao_id}' é do tipo '{tipo_inspecao}'; o {tipo} só é gerado para "
            f"inspeções do tipo '{tipo}'.",
            type_suffix=f"inspecao-nao-{tipo.lower()}",
        )


# --- emissão ----------------------------------------------------------------------------


async def emitir_relatorio(
    db: AsyncSession,
    inspecao_id: uuid.UUID,
    tipo: str,
    storage: StorageClient,
    renderizador: RenderizadorProtocol | None = None,
) -> Relatorio:
    """Gera PDF e DOCX do `tipo` e registra uma nova versão de `Relatorio`.

    Sem `renderizador`, usa o do emissor (`Emissor.criar_renderizador`).
    """
    emissor = obter_emissor(tipo)
    await _exigir_inspecao_do_tipo(db, inspecao_id, emissor.tipo)
    contexto = await emissor.montar_contexto(db, inspecao_id)
    faltantes = emissor.validar_contexto(contexto)
    if faltantes:
        if emissor.tipo == TIPO_RFO:
            raise RfoContextoIncompletoError(faltantes)
        raise ContextoIncompletoError(emissor.tipo, faltantes)
    renderizador = renderizador or emissor.criar_renderizador()
    if emissor.anexar_do_storage is not None:
        await asyncio.to_thread(emissor.anexar_do_storage, contexto, storage)
    fotos = await asyncio.to_thread(_baixar_fotos, storage, emissor.extrair_fotos(contexto))
    pdf = await asyncio.to_thread(renderizador.gerar_pdf, contexto, fotos)
    docx = await asyncio.to_thread(renderizador.gerar_docx, contexto, fotos)

    # FOR NO KEY UPDATE: serializa emissões da mesma inspeção (versão única) sem
    # bloquear inserts de visitas/ocorrências (que só pegam FOR KEY SHARE no pai).
    await db.execute(select(Inspecao.id).where(Inspecao.id == inspecao_id).with_for_update(key_share=True))
    versoes = (
        await db.execute(
            select(Relatorio.versao).where(Relatorio.inspecao_id == inspecao_id, Relatorio.tipo == emissor.tipo)
        )
    ).scalars().all()
    versao = proxima_versao(list(versoes))
    pdf_key = chave_relatorio(inspecao_id, versao, "pdf", emissor.tipo)
    docx_key = chave_relatorio(inspecao_id, versao, "docx", emissor.tipo)

    gravadas: list[str] = []
    try:
        for chave, conteudo, content_type in (
            (pdf_key, pdf, CONTENT_TYPE_PDF),
            (docx_key, docx, CONTENT_TYPE_DOCX),
        ):
            await asyncio.to_thread(
                storage.upload, chave, conteudo, content_type, max_size_bytes=MAX_RELATORIO_SIZE_BYTES
            )
            gravadas.append(chave)

        relatorio = Relatorio(
            inspecao_id=inspecao_id,
            versao=versao,
            tipo=emissor.tipo,
            status=STATUS_EMITIDO,
            pdf_key=pdf_key,
            docx_key=docx_key,
            emitido_em=datetime.now(UTC),
        )
        db.add(relatorio)
        await db.commit()
    except Exception:
        await db.rollback()
        await asyncio.to_thread(_apagar_sem_falhar, storage, gravadas)
        raise
    await db.refresh(relatorio)
    return relatorio


async def emitir_rfo(
    db: AsyncSession,
    inspecao_id: uuid.UUID,
    storage: StorageClient,
    renderizador: RenderizadorProtocol,
) -> Relatorio:
    """Compatibilidade (BL-13): `emitir_relatorio` com tipo `RFO`."""
    return await emitir_relatorio(db, inspecao_id, TIPO_RFO, storage, renderizador)


# --- consulta e download (equipe interna) -------------------------------------------------


async def listar_relatorios(db: AsyncSession, inspecao_id: uuid.UUID) -> list[Relatorio]:
    """Versões emitidas da inspeção (mais recente primeiro); 404 se a inspeção não existe."""
    if (await db.execute(select(Inspecao.id).where(Inspecao.id == inspecao_id))).scalar_one_or_none() is None:
        raise NotFoundError(f"Inspeção '{inspecao_id}' não encontrada.", type_suffix="inspecao-nao-encontrada")
    result = await db.execute(
        select(Relatorio)
        .where(Relatorio.inspecao_id == inspecao_id)
        .order_by(Relatorio.emitido_em.desc().nullslast(), Relatorio.tipo, Relatorio.versao.desc())
    )
    return list(result.scalars().all())


async def gerar_url_download(
    db: AsyncSession,
    inspecao_id: uuid.UUID,
    relatorio_id: uuid.UUID,
    formato: str,
    storage: StorageClient,
) -> PortalDownloadRead:
    """URL pré-assinada do PDF/DOCX; a mesma lógica do portal, mas escopada pela inspeção.

    404 se o formato não é suportado, se o relatório não pertence à inspeção ou se
    não há arquivo daquele formato.
    """
    campo_key = portal_service.campo_do_formato(formato)
    relatorio = (
        await db.execute(
            select(Relatorio).where(Relatorio.id == relatorio_id, Relatorio.inspecao_id == inspecao_id)
        )
    ).scalar_one_or_none()
    if relatorio is None:
        raise NotFoundError(
            f"Relatório '{relatorio_id}' não encontrado na inspeção '{inspecao_id}'.",
            type_suffix="relatorio-nao-encontrado",
        )
    return portal_service.url_assinada_do_relatorio(relatorio, campo_key, formato, storage)
