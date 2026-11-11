"""Emissão do RFO (PDF + DOCX) a partir do banco (BL-13, RF-06, RN-18/DEC-27).

Fluxo: `montar_contexto_rfo` (404/409) → baixa as fotos do storage → renderiza
PDF e DOCX (renderizador injetável) → trava a inspeção → calcula a próxima
versão → grava os arquivos em chaves determinísticas do servidor → cria um
`Relatorio` novo por emissão (as versões anteriores ficam preservadas).

O renderizador padrão importa `rfo_pipeline` (WeasyPrint) sob demanda: sem as
bibliotecas nativas (GTK/Pango, ex.: Windows fora do container) a emissão falha
com 503 `gerador-relatorio-indisponivel`, nunca com 500.
"""
from __future__ import annotations

import asyncio
import logging
import re
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, DomainError
from app.models import Inspecao, Relatorio
from app.services.report_generator.rfo_contexto import TIPO_RFO, montar_contexto_rfo
from app.services.storage import ObjectNotFoundError, StorageClient

logger = logging.getLogger(__name__)

STATUS_EMITIDO = "emitido"
CONTENT_TYPE_PDF = "application/pdf"
CONTENT_TYPE_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
# Um RFO com muitas fotos passa fácil do limite de foto de `StorageClient.upload`.
MAX_RELATORIO_SIZE_BYTES = 200 * 1024 * 1024
_VERSAO_RE = re.compile(r"^V(\d+)$")


class GeradorIndisponivelError(DomainError):
    """Motor de renderização sem dependências nativas. Vira HTTP 503."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            detail,
            type_suffix="gerador-relatorio-indisponivel",
            title="Gerador de relatório indisponível",
            status_code=503,
        )


class RenderizadorRFO(Protocol):
    def gerar_pdf(self, contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes: ...

    def gerar_docx(self, contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes: ...


class RenderizadorRFOPadrao:
    """Adapta `rfo_pipeline` (que escreve em arquivo) para devolver bytes."""

    @staticmethod
    def _pipeline() -> Any:
        try:
            from app.services.report_generator import rfo_pipeline
        except (ImportError, OSError) as exc:  # OSError: libpango/libgobject ausentes
            logger.warning("WeasyPrint indisponível para gerar o RFO: %s", exc)
            raise GeradorIndisponivelError(
                "O gerador de PDF (WeasyPrint) não está disponível neste servidor: faltam as "
                "bibliotecas nativas GTK/Pango. Gere o relatório pelo container da API."
            ) from exc
        return rfo_pipeline

    def _gerar(self, metodo: str, extensao: str, contexto: dict[str, Any], fotos: dict[str, bytes]) -> bytes:
        pipeline = self._pipeline()
        fotos_otimizadas = {chave: pipeline.otimizar_imagem(conteudo) for chave, conteudo in fotos.items()}
        with tempfile.TemporaryDirectory(prefix="rfo-") as pasta:
            destino = Path(pasta) / f"rfo.{extensao}"
            getattr(pipeline, metodo)(contexto, fotos_otimizadas, destino)
            return destino.read_bytes()

    def gerar_pdf(self, contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes:
        return self._gerar("gerar_pdf", "pdf", contexto, fotos_bytes)

    def gerar_docx(self, contexto: dict[str, Any], fotos_bytes: dict[str, bytes]) -> bytes:
        return self._gerar("gerar_docx", "docx", contexto, fotos_bytes)


def chave_relatorio(inspecao_id: uuid.UUID, versao: str, extensao: str) -> str:
    """Chave determinística no storage: `relatorios/{inspecao_id}/rfo-v01.pdf`."""
    return f"relatorios/{inspecao_id}/rfo-{versao.lower()}.{extensao}"


def proxima_versao(versoes: list[str]) -> str:
    """`V01`, `V02`... Ignora valores fora do padrão (ex.: cargas manuais antigas)."""
    numeros = [int(m.group(1)) for v in versoes if (m := _VERSAO_RE.match(v or ""))]
    return f"V{max(numeros, default=0) + 1:02d}"


def storage_keys_das_fotos(contexto: dict[str, Any]) -> list[str]:
    """Fotos que o `rfo_pipeline` embute: só as das visitas (o template não imprime ocorrências)."""
    chaves = [f["storage_key"] for v in contexto.get("visitas", []) for f in v.get("fotos", [])]
    return list(dict.fromkeys(chaves))


def _baixar_fotos(storage: StorageClient, chaves: list[str]) -> dict[str, bytes]:
    fotos: dict[str, bytes] = {}
    for chave in chaves:
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
            logger.exception("Falha ao remover '%s' após erro na emissão do RFO", chave)


async def emitir_rfo(
    db: AsyncSession,
    inspecao_id: uuid.UUID,
    storage: StorageClient,
    renderizador: RenderizadorRFO,
) -> Relatorio:
    """Gera PDF e DOCX do RFO e registra uma nova versão de `Relatorio`."""
    contexto = await montar_contexto_rfo(db, inspecao_id)
    fotos = await asyncio.to_thread(_baixar_fotos, storage, storage_keys_das_fotos(contexto))
    pdf = await asyncio.to_thread(renderizador.gerar_pdf, contexto, fotos)
    docx = await asyncio.to_thread(renderizador.gerar_docx, contexto, fotos)

    # FOR NO KEY UPDATE: serializa emissões da mesma inspeção (versão única) sem
    # bloquear inserts de visitas/ocorrências (que só pegam FOR KEY SHARE no pai).
    await db.execute(select(Inspecao.id).where(Inspecao.id == inspecao_id).with_for_update(key_share=True))
    versoes = (
        await db.execute(
            select(Relatorio.versao).where(Relatorio.inspecao_id == inspecao_id, Relatorio.tipo == TIPO_RFO)
        )
    ).scalars().all()
    versao = proxima_versao(list(versoes))
    pdf_key = chave_relatorio(inspecao_id, versao, "pdf")
    docx_key = chave_relatorio(inspecao_id, versao, "docx")

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
            tipo=TIPO_RFO,
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
