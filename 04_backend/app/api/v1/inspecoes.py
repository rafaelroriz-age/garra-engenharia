"""Endpoints de Inspeção (BL-10, RF-03, `00_docs/arquitetura.md` Seção 4).

- `GET /inspecoes/{id}` — detalhe da inspeção com visitas (ordenadas por `seq_numero`).
- `POST /inspecoes/{id}/visitas` — cria visita de fiscalização (RN-01, RN-02).

Protegidos por `get_current_user` (BL-06).
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Inspecao, Usuario, Visita
from app.schemas.inspecao import InspecaoDetalhe
from app.schemas.visita import VisitaComDetalhes, VisitaCreatePayload
from app.services import visita_service
from app.services import inspecao_service

router = APIRouter(prefix="/api/v1/inspecoes", tags=["inspecoes"])


@router.get("/{inspecao_id}", response_model=InspecaoDetalhe)
async def obter_inspecao(
    inspecao_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> Inspecao:
    """Detalhe da inspeção com visitas, equipe, medições e fotos vinculadas."""
    return await inspecao_service.obter_por_id(db, inspecao_id)


@router.post("/{inspecao_id}/visitas", response_model=VisitaComDetalhes, status_code=status.HTTP_201_CREATED)
async def criar_visita(
    inspecao_id: uuid.UUID,
    dados: VisitaCreatePayload,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
) -> Visita:
    """Cria uma visita de fiscalização, com `seq_numero` atribuído automaticamente (RN-01)."""
    return await visita_service.criar_visita(db, inspecao_id, dados)
