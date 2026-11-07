"""Repository de `Visita`, `VisitaMaoObra` e `VisitaMedicao` (BL-10, RF-03, RN-01, RN-02)."""
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Inspecao, Visita, VisitaMaoObra, VisitaMedicao
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


async def _recarregar_com_detalhes(db: AsyncSession, visita_id: uuid.UUID) -> Visita:
    result = await db.execute(
        select(Visita)
        .options(*_DETALHE_OPTIONS)
        .where(Visita.id == visita_id)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


async def bloquear_inspecao(db: AsyncSession, inspecao_id: uuid.UUID) -> None:
    """`SELECT ... FOR UPDATE` na Inspeção: serializa criações/mudanças de data concorrentes na
    mesma inspeção até o commit, para que `max(seq_numero)+1` e a checagem de data não corram
    (DEC-38 B). O UNIQUE no banco segue como rede de segurança."""
    await db.execute(select(Inspecao.id).where(Inspecao.id == inspecao_id).with_for_update())


async def existe_visita_na_data(
    db: AsyncSession, inspecao_id: uuid.UUID, data: date, *, exceto_id: uuid.UUID | None = None
) -> bool:
    stmt = select(Visita.id).where(Visita.inspecao_id == inspecao_id, Visita.data == data)
    if exceto_id is not None:
        stmt = stmt.where(Visita.id != exceto_id)
    return (await db.execute(stmt.limit(1))).first() is not None


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
    """Cria a visita; o chamador deve ter chamado `bloquear_inspecao` na mesma transação."""
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
    return await _recarregar_com_detalhes(db, visita.id)


async def update_visita(db: AsyncSession, visita: Visita, dados: VisitaUpdatePayload) -> Visita:
    """Atualização parcial (DEC-38 D): só os campos enviados no payload são alterados."""
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(visita, campo, valor)
    await db.commit()
    return await _recarregar_com_detalhes(db, visita.id)


# ---------------------------------------------------------------- Mão de obra

async def list_mao_obra(db: AsyncSession, visita_id: uuid.UUID) -> list[VisitaMaoObra]:
    result = await db.execute(
        select(VisitaMaoObra).where(VisitaMaoObra.visita_id == visita_id).order_by(VisitaMaoObra.funcao)
    )
    return list(result.scalars().all())


async def get_mao_obra(db: AsyncSession, visita_id: uuid.UUID, item_id: uuid.UUID) -> VisitaMaoObra | None:
    result = await db.execute(
        select(VisitaMaoObra).where(VisitaMaoObra.id == item_id, VisitaMaoObra.visita_id == visita_id)
    )
    return result.scalar_one_or_none()


async def add_mao_obra(
    db: AsyncSession, visita_id: uuid.UUID, dados: VisitaMaoObraCreatePayload
) -> VisitaMaoObra:
    registro = VisitaMaoObra(visita_id=visita_id, funcao=dados.funcao, quantidade=dados.quantidade)
    db.add(registro)
    await db.commit()
    await db.refresh(registro)
    return registro


async def update_mao_obra(
    db: AsyncSession, registro: VisitaMaoObra, dados: VisitaMaoObraCreatePayload
) -> VisitaMaoObra:
    registro.funcao = dados.funcao
    registro.quantidade = dados.quantidade
    await db.commit()
    await db.refresh(registro)
    return registro


# ---------------------------------------------------------------- Medições

async def list_medicoes(db: AsyncSession, visita_id: uuid.UUID) -> list[VisitaMedicao]:
    result = await db.execute(
        select(VisitaMedicao).where(VisitaMedicao.visita_id == visita_id).order_by(VisitaMedicao.descricao)
    )
    return list(result.scalars().all())


async def get_medicao(db: AsyncSession, visita_id: uuid.UUID, item_id: uuid.UUID) -> VisitaMedicao | None:
    result = await db.execute(
        select(VisitaMedicao).where(VisitaMedicao.id == item_id, VisitaMedicao.visita_id == visita_id)
    )
    return result.scalar_one_or_none()


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


async def update_medicao(
    db: AsyncSession, registro: VisitaMedicao, dados: VisitaMedicaoCreatePayload
) -> VisitaMedicao:
    registro.descricao = dados.descricao
    registro.quantidade = dados.quantidade
    registro.unidade = dados.unidade
    await db.commit()
    await db.refresh(registro)
    return registro


async def delete_item(db: AsyncSession, registro: VisitaMaoObra | VisitaMedicao) -> None:
    await db.delete(registro)
    await db.commit()
