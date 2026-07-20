"""Repository de `Contrato` (BL-09, RF-02, RF-12, RN-06, RN-09).

Concentra a criação/atualização em cascata de `ContratoExecutor` e
`ContratoNbr` (N por Contrato) e da `Inspecao` originada (relação 1:1,
`00_docs/arquitetura.md` Seção 3), sempre em uma única transação (Unit of
Work, Seção 9.11).
"""
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Contrato, ContratoExecutor, ContratoNbr, Inspecao
from app.schemas.contrato import ContratoCreatePayload, ContratoUpdatePayload

_DETALHE_OPTIONS = (
    selectinload(Contrato.executores),
    selectinload(Contrato.nbrs),
    selectinload(Contrato.inspecao),
)


async def list_paginated(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    tipo_servico: str | None = None,
    status_contrato: str | None = None,
    edificacao_id: uuid.UUID | None = None,
) -> tuple[list[Contrato], int]:
    """Lista contratos paginados, com filtro opcional por tipo, status e edificação."""
    base_stmt = select(Contrato)
    count_stmt = select(func.count()).select_from(Contrato)

    if tipo_servico:
        base_stmt = base_stmt.where(Contrato.tipo_servico == tipo_servico)
        count_stmt = count_stmt.where(Contrato.tipo_servico == tipo_servico)
    if status_contrato:
        base_stmt = base_stmt.where(Contrato.status == status_contrato)
        count_stmt = count_stmt.where(Contrato.status == status_contrato)
    if edificacao_id:
        base_stmt = base_stmt.where(Contrato.edificacao_id == edificacao_id)
        count_stmt = count_stmt.where(Contrato.edificacao_id == edificacao_id)

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        base_stmt.order_by(Contrato.numero).offset((page - 1) * page_size).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_by_id(db: AsyncSession, contrato_id: uuid.UUID) -> Contrato | None:
    """Busca um contrato pelo id, com executoras, NBRs e a Inspeção originada carregadas."""
    result = await db.execute(
        select(Contrato).options(*_DETALHE_OPTIONS).where(Contrato.id == contrato_id)
    )
    return result.scalar_one_or_none()


async def create_with_executores_nbrs(db: AsyncSession, dados: ContratoCreatePayload) -> Contrato:
    """Cria o Contrato, suas ContratoExecutor/ContratoNbr e a Inspecao 1:1, em uma única transação."""
    contrato_dados = dados.model_dump(exclude={"executores", "nbrs"})
    contrato = Contrato(**contrato_dados)
    db.add(contrato)
    await db.flush()  # garante contrato.id antes de criar os filhos

    for executor in dados.executores:
        db.add(ContratoExecutor(contrato_id=contrato.id, **executor.model_dump()))
    for nbr in dados.nbrs:
        db.add(ContratoNbr(contrato_id=contrato.id, **nbr.model_dump()))

    inspecao = Inspecao(contrato_id=contrato.id, tipo=contrato.tipo_servico, status="em_andamento")
    db.add(inspecao)

    await db.commit()

    result = await db.execute(
        select(Contrato).options(*_DETALHE_OPTIONS).where(Contrato.id == contrato.id)
    )
    return result.scalar_one()


async def update_with_executores_nbrs(
    db: AsyncSession, contrato: Contrato, dados: ContratoUpdatePayload
) -> Contrato:
    """Atualiza o Contrato e substitui integralmente suas ContratoExecutor/ContratoNbr."""
    contrato_dados = dados.model_dump(exclude={"executores", "nbrs"})
    for campo, valor in contrato_dados.items():
        setattr(contrato, campo, valor)

    await db.execute(delete(ContratoExecutor).where(ContratoExecutor.contrato_id == contrato.id))
    await db.execute(delete(ContratoNbr).where(ContratoNbr.contrato_id == contrato.id))

    for executor in dados.executores:
        db.add(ContratoExecutor(contrato_id=contrato.id, **executor.model_dump()))
    for nbr in dados.nbrs:
        db.add(ContratoNbr(contrato_id=contrato.id, **nbr.model_dump()))

    if contrato.inspecao is not None:
        contrato.inspecao.tipo = contrato.tipo_servico

    await db.commit()

    # `populate_existing=True`: a instância `contrato` pode já ter `executores`/`nbrs`
    # carregados na identity map da sessão (do `get_by_id` que a originou); sem isso, o
    # `selectinload` abaixo não sobrescreveria a coleção antiga em memória com os novos
    # registros criados após o delete+insert acima.
    result = await db.execute(
        select(Contrato)
        .options(*_DETALHE_OPTIONS)
        .where(Contrato.id == contrato.id)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()
