"""Repository de `Visita`, `VisitaMaoObra` e `VisitaMedicao` (BL-10, RF-03, RN-01, RN-02)."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Visita, VisitaMaoObra, VisitaMedicao
from app.schemas.visita import VisitaCreatePayload, VisitaUpdatePayload
from app.schemas.visita_mao_obra import VisitaMaoObraCreatePayload
from app.schemas.visita_medicao import VisitaMedicaoCreatePayload

_DETALHE_OPTIONS = (
    selectinload(Visita.mao_obra),
    selectinload(Visita.medicoes),
    selectinload(Visita.fotos),
)


async def get_by_id(db: AsyncSession, visita_id: uuid.UUID) -> Visita | None:
    result = await db.execute(select(Visita).options(*_DETALHE_OPTIONS).where(Visita.id == visita_id))
    return result.scalar_one_or_none()


async def _proximo_seq_numero(db: AsyncSession, inspecao_id: uuid.UUID) -> int:
    """Próximo `seq_numero` sequencial dentro da Inspeção (RN-01: uma visita por dia de obra)."""
    maior_atual = (
        await db.execute(select(func.max(Visita.seq_numero)).where(Visita.inspecao_id == inspecao_id))
    ).scalar_one()
    return (maior_atual or 0) + 1


async def create_visita(
    db: AsyncSession,
    inspecao_id: uuid.UUID,
    dados: VisitaCreatePayload,
    *,
    criado_por_id: uuid.UUID | None = None,
) -> Visita:
    seq_numero = await _proximo_seq_numero(db, inspecao_id)
    visita = Visita(
        inspecao_id=inspecao_id,
        data=dados.data,
        servicos_executados=dados.servicos_executados,
        observacoes=dados.observacoes,
        seq_numero=seq_numero,
        criado_por_id=criado_por_id,
    )
    db.add(visita)
    await db.commit()

    result = await db.execute(select(Visita).options(*_DETALHE_OPTIONS).where(Visita.id == visita.id))
    return result.scalar_one()


async def update_visita(db: AsyncSession, visita: Visita, dados: VisitaUpdatePayload) -> Visita:
    visita.data = dados.data
    visita.servicos_executados = dados.servicos_executados
    visita.observacoes = dados.observacoes
    await db.commit()
    await db.refresh(visita)
    return visita


async def add_mao_obra(
    db: AsyncSession, visita_id: uuid.UUID, dados: VisitaMaoObraCreatePayload
) -> VisitaMaoObra:
    registro = VisitaMaoObra(visita_id=visita_id, funcao=dados.funcao, quantidade=dados.quantidade)
    db.add(registro)
    await db.commit()
    await db.refresh(registro)
    return registro


async def add_medicao(
    db: AsyncSession, visita_id: uuid.UUID, dados: VisitaMedicaoCreatePayload
) -> VisitaMedicao:
    registro = VisitaMedicao(
        visita_id=visita_id, descricao=dados.descricao, quantidade=dados.quantidade, unidade=dados.unidade
    )
    db.add(registro)
    await db.commit()
    await db.refresh(registro)
    return registro
