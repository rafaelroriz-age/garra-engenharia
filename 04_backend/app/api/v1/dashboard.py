"""Endpoints de dashboard (BL-16, RF-07)."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_equipe
from app.core.database import get_db
from app.models import Edificacao, Usuario
from app.schemas.dashboard import DashboardEdificacaoRead
from app.services import edificacao_service

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/edificacoes/{edificacao_id}/dashboard", response_model=DashboardEdificacaoRead)
async def obter_dashboard_edificacao(
    edificacao_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_equipe),
) -> DashboardEdificacaoRead:
    """Retorna um agregado simples de saúde da edificação para o dashboard do frontend."""
    return await edificacao_service.obter_dashboard(db, edificacao_id)
