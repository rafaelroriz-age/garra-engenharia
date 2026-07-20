"""Service Layer de `Edificacao` (BL-08, RF-01).

Concentra as regras de negócio do CRUD de Edificações; o repository
(`app.repositories.edificacao_repository`) só executa queries.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Edificacao
from app.repositories import edificacao_repository
from app.schemas.edificacao import EdificacaoCreate, EdificacaoUpdate


async def listar(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    nome: str | None = None,
    endereco: str | None = None,
) -> tuple[list[Edificacao], int]:
    return await edificacao_repository.list_paginated(
        db, page=page, page_size=page_size, nome=nome, endereco=endereco
    )


async def obter_por_id(db: AsyncSession, edificacao_id: uuid.UUID) -> Edificacao:
    edificacao = await edificacao_repository.get_by_id(db, edificacao_id)
    if edificacao is None:
        raise NotFoundError(
            f"Edificação '{edificacao_id}' não encontrada.",
            type_suffix="edificacao-nao-encontrada",
        )
    return edificacao


async def criar(db: AsyncSession, dados: EdificacaoCreate) -> Edificacao:
    return await edificacao_repository.create(db, dados)


async def atualizar(db: AsyncSession, edificacao_id: uuid.UUID, dados: EdificacaoUpdate) -> Edificacao:
    edificacao = await obter_por_id(db, edificacao_id)
    return await edificacao_repository.update(db, edificacao, dados)
