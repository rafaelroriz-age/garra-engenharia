from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_cliente_responsavel, get_current_user, require_role
from app.core.database import get_db
from app.models import Contrato, Edificacao
from app.schemas import EdificacaoRead

router = APIRouter(prefix="/api/v1/portal", tags=["portal"])


@router.get("/edificacoes", response_model=list[EdificacaoRead], summary="Lista edificações do contratante")
async def listar_edificacoes_portal(
    _current_user=Depends(require_role("cliente")),
    responsavel=Depends(get_current_cliente_responsavel),
    db: AsyncSession = Depends(get_db),
) -> list[Edificacao]:
    """Retorna apenas as edificações vinculadas aos contratos do contratante logado."""
    result = await db.execute(
        select(Edificacao)
        .join(Contrato, Contrato.edificacao_id == Edificacao.id)
        .where(Contrato.contratante_id == responsavel.id)
    )
    return list(result.scalars().all())
