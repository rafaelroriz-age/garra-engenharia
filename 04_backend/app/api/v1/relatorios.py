"""Emissão de relatórios (BL-13, RF-06).

- `POST /inspecoes/{id}/relatorios/rfo` — gera PDF e DOCX do RFO, grava no
  storage e registra uma nova versão de `Relatorio` (visível no Portal do
  Cliente, BL-33).

Só o auditor emite relatório (RN-18, DEC-27/ADR-14): `auxiliar` e `cliente`
recebem 403. O renderizador é uma dependency (`get_renderizador_rfo`) para os
testes injetarem um fake sem WeasyPrint.
"""
import uuid

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auditor
from app.core.database import get_db
from app.models import Usuario
from app.schemas.relatorio import RelatorioEmitidoRead, RelatorioEmitirPayload
from app.services import relatorio_service
from app.services.relatorio_service import RenderizadorRFO, RenderizadorRFOPadrao
from app.services.storage import StorageClient, get_storage_client

router = APIRouter(prefix="/api/v1/inspecoes", tags=["relatorios"])


def get_renderizador_rfo() -> RenderizadorRFO:
    """Dependency do renderizador do RFO; substitua em testes via `dependency_overrides`."""
    return RenderizadorRFOPadrao()


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
    renderizador: RenderizadorRFO = Depends(get_renderizador_rfo),
) -> RelatorioEmitidoRead:
    relatorio = await relatorio_service.emitir_rfo(db, inspecao_id, storage, renderizador)
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
