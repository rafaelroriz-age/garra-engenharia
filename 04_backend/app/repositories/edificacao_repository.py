"""Repository de `Edificacao` (BL-08, RF-01).

Isola as queries SQLAlchemy consumidas por `app.services.edificacao_service`.
"""
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Edificacao
from app.schemas.edificacao import EdificacaoCreate, EdificacaoUpdate


async def list_paginated(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    nome: str | None = None,
    endereco: str | None = None,
) -> tuple[list[Edificacao], int]:
    """Lista edificações paginadas, com filtro opcional por nome/endereço (busca parcial)."""
    filtros = []
    if nome:
        filtros.append(Edificacao.nome.ilike(f"%{nome}%"))
    if endereco:
        filtros.append(Edificacao.endereco.ilike(f"%{endereco}%"))

    base_stmt = select(Edificacao)
    count_stmt = select(func.count()).select_from(Edificacao)
    if filtros:
        base_stmt = base_stmt.where(or_(*filtros) if len(filtros) > 1 else filtros[0])
        count_stmt = count_stmt.where(or_(*filtros) if len(filtros) > 1 else filtros[0])

    total = (await db.execute(count_stmt)).scalar_one()

    result = await db.execute(
        base_stmt.order_by(Edificacao.nome).offset((page - 1) * page_size).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_by_id(db: AsyncSession, edificacao_id: uuid.UUID) -> Edificacao | None:
    """Busca uma edificação pelo id, já carregando o histórico de Contratos."""
    result = await db.execute(
        select(Edificacao)
        .options(selectinload(Edificacao.contratos))
        .where(Edificacao.id == edificacao_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, dados: EdificacaoCreate) -> Edificacao:
    edificacao = Edificacao(**dados.model_dump())
    db.add(edificacao)
    await db.commit()
    await db.refresh(edificacao)
    return edificacao


# DEC-59: `cidade`/`uf` ausentes no corpo do PUT são preservados; enviados (inclusive `null`) são gravados.
CAMPOS_PRESERVAVEIS_AUSENTES = ("cidade", "uf")


async def update(db: AsyncSession, edificacao: Edificacao, dados: EdificacaoUpdate) -> Edificacao:
    campos = dados.model_dump()
    for campo in CAMPOS_PRESERVAVEIS_AUSENTES:
        if campo not in dados.model_fields_set:
            campos.pop(campo)
    for campo, valor in campos.items():
        setattr(edificacao, campo, valor)
    await db.commit()
    await db.refresh(edificacao)
    return edificacao
