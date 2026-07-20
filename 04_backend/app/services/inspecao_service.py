"""Service Layer de `Inspecao` (BL-10, RF-03)."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Inspecao
from app.repositories import inspecao_repository


async def obter_por_id(db: AsyncSession, inspecao_id: uuid.UUID) -> Inspecao:
    inspecao = await inspecao_repository.get_by_id(db, inspecao_id)
    if inspecao is None:
        raise NotFoundError(f"Inspeção '{inspecao_id}' não encontrada.", type_suffix="inspecao-nao-encontrada")
    return inspecao
