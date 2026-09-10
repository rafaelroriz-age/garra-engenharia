"""Endpoints de Visita, Mão de Obra e Medição (BL-10, RF-03, RN-01, RN-02).

- `PUT /visitas/{id}` — atualiza visita (data, serviços executados, observações).
- `POST /visitas/{id}/mao-obra` — adiciona registro de mão de obra.
- `POST /visitas/{id}/medicoes` — adiciona medição.

Dados de campo: liberados à equipe (`auditor`/`auxiliar`) — RN-18, DEC-27.
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_equipe
from app.core.database import get_db
from app.models import Usuario, Visita, VisitaMaoObra, VisitaMedicao
from app.schemas.visita import VisitaComDetalhes, VisitaUpdatePayload
from app.schemas.visita_mao_obra import VisitaMaoObraCreatePayload, VisitaMaoObraRead
from app.schemas.visita_medicao import VisitaMedicaoCreatePayload, VisitaMedicaoRead
from app.services import visita_service

router = APIRouter(prefix="/api/v1/visitas", tags=["visitas"])


@router.put("/{visita_id}", response_model=VisitaComDetalhes)
async def atualizar_visita(
    visita_id: uuid.UUID,
    dados: VisitaUpdatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> Visita:
    """Atualiza data, serviços executados e observações de uma visita."""
    return await visita_service.atualizar_visita(db, visita_id, dados)


@router.post(
    "/{visita_id}/mao-obra", response_model=VisitaMaoObraRead, status_code=status.HTTP_201_CREATED
)
async def adicionar_mao_obra(
    visita_id: uuid.UUID,
    dados: VisitaMaoObraCreatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> VisitaMaoObra:
    """Adiciona um registro de mão de obra (função + quantidade) a uma visita."""
    return await visita_service.adicionar_mao_obra(db, visita_id, dados)


@router.post(
    "/{visita_id}/medicoes", response_model=VisitaMedicaoRead, status_code=status.HTTP_201_CREATED
)
async def adicionar_medicao(
    visita_id: uuid.UUID,
    dados: VisitaMedicaoCreatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> VisitaMedicao:
    """Adiciona uma medição (descrição + quantidade + unidade) a uma visita."""
    return await visita_service.adicionar_medicao(db, visita_id, dados)
