"""Service Layer de `Visita`, `VisitaMaoObra` e `VisitaMedicao` (BL-10, RF-03, RN-01, RN-02)."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Visita, VisitaMaoObra, VisitaMedicao
from app.repositories import visita_repository
from app.services import inspecao_service
from app.schemas.visita import VisitaCreatePayload, VisitaUpdatePayload
from app.schemas.visita_mao_obra import VisitaMaoObraCreatePayload
from app.schemas.visita_medicao import VisitaMedicaoCreatePayload


async def obter_por_id(db: AsyncSession, visita_id: uuid.UUID) -> Visita:
    visita = await visita_repository.get_by_id(db, visita_id)
    if visita is None:
        raise NotFoundError(f"Visita '{visita_id}' não encontrada.", type_suffix="visita-nao-encontrada")
    return visita


async def criar_visita(
    db: AsyncSession,
    inspecao_id: uuid.UUID,
    dados: VisitaCreatePayload,
    *,
    criado_por_id: uuid.UUID | None = None,
) -> Visita:
    await inspecao_service.obter_por_id(db, inspecao_id)  # garante que a Inspeção existe (404 caso contrário)
    return await visita_repository.create_visita(db, inspecao_id, dados, criado_por_id=criado_por_id)


async def atualizar_visita(db: AsyncSession, visita_id: uuid.UUID, dados: VisitaUpdatePayload) -> Visita:
    visita = await obter_por_id(db, visita_id)
    return await visita_repository.update_visita(db, visita, dados)


async def adicionar_mao_obra(
    db: AsyncSession, visita_id: uuid.UUID, dados: VisitaMaoObraCreatePayload
) -> VisitaMaoObra:
    await obter_por_id(db, visita_id)
    return await visita_repository.add_mao_obra(db, visita_id, dados)


async def adicionar_medicao(
    db: AsyncSession, visita_id: uuid.UUID, dados: VisitaMedicaoCreatePayload
) -> VisitaMedicao:
    await obter_por_id(db, visita_id)
    return await visita_repository.add_medicao(db, visita_id, dados)
