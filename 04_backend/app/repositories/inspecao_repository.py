"""Repository de `Inspecao` (BL-10, RF-03)."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Inspecao, Visita


async def get_by_id(db: AsyncSession, inspecao_id: uuid.UUID) -> Inspecao | None:
    """Busca a Inspeção pelo id, com as Visitas (e seus detalhes) já carregadas, ordenadas por `seq_numero`."""
    result = await db.execute(
        select(Inspecao)
        .options(
            selectinload(Inspecao.visitas).selectinload(Visita.mao_obra),
            selectinload(Inspecao.visitas).selectinload(Visita.medicoes),
            selectinload(Inspecao.visitas).selectinload(Visita.fotos),
        )
        .where(Inspecao.id == inspecao_id)
    )
    inspecao = result.scalar_one_or_none()
    if inspecao is not None:
        inspecao.visitas.sort(key=lambda visita: visita.seq_numero)
    return inspecao
