"""Emissão, listagem e download de relatórios (BL-13, V1-02, RF-06).

- `POST /inspecoes/{id}/relatorios/rfo` — atalho do BL-13, igual a `.../relatorios/RFO`.
- `POST /inspecoes/{id}/relatorios/{tipo}` — gera PDF e DOCX do tipo (registrado em
  `relatorio_service.EMISSORES`), grava no storage e registra uma nova versão de
  `Relatorio` (visível no Portal do Cliente, BL-33). Tipo não registrado → 422
  com os tipos disponíveis; tipo diferente do da inspeção → 409.
- `GET /inspecoes/{id}/relatorios` — versões emitidas da inspeção.
- `GET /inspecoes/{id}/relatorios/{relatorio_id}/download/{formato}` — URL
  pré-assinada (pdf|docx).

Só o auditor emite relatório (RN-18, DEC-27/ADR-14): `auxiliar` e `cliente`
recebem 403. Listagem e download são da equipe (`auditor` e `auxiliar`); o
cliente usa o portal. Os renderizadores são dependencies (`get_renderizador_rfo`,
`get_renderizador_por_tipo`) para os testes injetarem fakes sem WeasyPrint.
"""
import uuid
from collections.abc import Callable

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auditor, require_equipe
from app.core.database import get_db
from app.models import Relatorio, Usuario
from app.schemas.relatorio import (
    RelatorioDownloadRead,
    RelatorioEmitidoRead,
    RelatorioEmitirPayload,
    RelatorioVersaoRead,
)
from app.services import relatorio_service
from app.services.relatorio_service import RenderizadorProtocol, RenderizadorRFOPadrao
from app.services.storage import StorageClient, get_storage_client

router = APIRouter(prefix="/api/v1/inspecoes", tags=["relatorios"])

FabricaRenderizador = Callable[[str], RenderizadorProtocol]


def get_renderizador_rfo() -> RenderizadorProtocol:
    """Dependency do renderizador do RFO; substitua em testes via `dependency_overrides`."""
    return RenderizadorRFOPadrao()


def get_renderizador_por_tipo() -> FabricaRenderizador:
    """Dependency `tipo -> renderizador` da rota genérica; substitua em testes."""
    return lambda tipo: relatorio_service.obter_emissor(tipo).criar_renderizador()


def _emitido(relatorio: Relatorio) -> RelatorioEmitidoRead:
    return RelatorioEmitidoRead(
        id=relatorio.id,
        inspecao_id=relatorio.inspecao_id,
        tipo=relatorio.tipo,
        versao=relatorio.versao,
        status=relatorio.status,
        tem_pdf=bool(relatorio.pdf_key),
        tem_docx=bool(relatorio.docx_key),
        criado_em=relatorio.emitido_em,
    )


@router.post(
    "/{inspecao_id}/relatorios/rfo",
    response_model=RelatorioEmitidoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Emite o RFO (PDF e DOCX) da inspeção como nova versão",
)
async def emitir_relatorio_rfo(
    inspecao_id: uuid.UUID,
    _dados: RelatorioEmitirPayload | None = Body(default=None),
    _usuario: Usuario = Depends(require_auditor),
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
    renderizador: RenderizadorProtocol = Depends(get_renderizador_rfo),
) -> RelatorioEmitidoRead:
    relatorio = await relatorio_service.emitir_rfo(db, inspecao_id, storage, renderizador)
    return _emitido(relatorio)


@router.post(
    "/{inspecao_id}/relatorios/{tipo}",
    response_model=RelatorioEmitidoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Emite o relatório do tipo (PDF e DOCX) da inspeção como nova versão",
)
async def emitir_relatorio_por_tipo(
    inspecao_id: uuid.UUID,
    tipo: str,
    _dados: RelatorioEmitirPayload | None = Body(default=None),
    _usuario: Usuario = Depends(require_auditor),
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
    fabrica: FabricaRenderizador = Depends(get_renderizador_por_tipo),
) -> RelatorioEmitidoRead:
    emissor = relatorio_service.obter_emissor(tipo)  # 422 antes de tocar no banco
    relatorio = await relatorio_service.emitir_relatorio(
        db, inspecao_id, emissor.tipo, storage, fabrica(emissor.tipo)
    )
    return _emitido(relatorio)


@router.get(
    "/{inspecao_id}/relatorios",
    response_model=list[RelatorioVersaoRead],
    summary="Lista as versões de relatório emitidas para a inspeção",
)
async def listar_relatorios(
    inspecao_id: uuid.UUID,
    _usuario: Usuario = Depends(require_equipe),
    db: AsyncSession = Depends(get_db),
) -> list[RelatorioVersaoRead]:
    return [
        RelatorioVersaoRead(
            id=r.id,
            tipo=r.tipo,
            versao=r.versao,
            status=r.status,
            emitido_em=r.emitido_em,
            tem_pdf=bool(r.pdf_key),
            tem_docx=bool(r.docx_key),
        )
        for r in await relatorio_service.listar_relatorios(db, inspecao_id)
    ]


@router.get(
    "/{inspecao_id}/relatorios/{relatorio_id}/download/{formato}",
    response_model=RelatorioDownloadRead,
    summary="URL pré-assinada de download do relatório (pdf|docx) para a equipe",
)
async def baixar_relatorio(
    inspecao_id: uuid.UUID,
    relatorio_id: uuid.UUID,
    formato: str,
    _usuario: Usuario = Depends(require_equipe),
    db: AsyncSession = Depends(get_db),
    storage: StorageClient = Depends(get_storage_client),
) -> RelatorioDownloadRead:
    download = await relatorio_service.gerar_url_download(db, inspecao_id, relatorio_id, formato.lower(), storage)
    return RelatorioDownloadRead(**download.model_dump())
