"""Service Layer de `Contrato` (BL-09, RF-02, RF-12, RN-06, RN-09).

Valida a existência das entidades referenciadas (Edificação, fiscal e
responsáveis das executoras) antes de delegar a criação/atualização em
cascata ao repository.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError, NotFoundError
from app.models import Contrato, Edificacao, Responsavel
from app.repositories import contrato_repository
from app.schemas.contrato import ContratoCreatePayload, ContratoUpdatePayload


async def _validar_referencias(db: AsyncSession, dados: ContratoCreatePayload | ContratoUpdatePayload) -> None:
    edificacao = await db.get(Edificacao, dados.edificacao_id)
    if edificacao is None:
        raise NotFoundError(
            f"Edificação '{dados.edificacao_id}' não encontrada.",
            type_suffix="edificacao-nao-encontrada",
        )

    ids_responsaveis = {dados.fiscal_id}
    for executor in dados.executores:
        ids_responsaveis.add(executor.responsavel_legal_id)
        if executor.rte_id is not None:
            ids_responsaveis.add(executor.rte_id)

    result = await db.execute(select(Responsavel.id).where(Responsavel.id.in_(ids_responsaveis)))
    encontrados = set(result.scalars().all())
    faltantes = ids_responsaveis - encontrados
    if faltantes:
        raise NotFoundError(
            f"Responsável(is) não encontrado(s): {', '.join(str(i) for i in faltantes)}.",
            type_suffix="responsavel-nao-encontrado",
        )


async def listar(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    tipo_servico: str | None = None,
    status_contrato: str | None = None,
    edificacao_id: uuid.UUID | None = None,
) -> tuple[list[Contrato], int]:
    return await contrato_repository.list_paginated(
        db,
        page=page,
        page_size=page_size,
        tipo_servico=tipo_servico,
        status_contrato=status_contrato,
        edificacao_id=edificacao_id,
    )


async def obter_por_id(db: AsyncSession, contrato_id: uuid.UUID) -> Contrato:
    contrato = await contrato_repository.get_by_id(db, contrato_id)
    if contrato is None:
        raise NotFoundError(f"Contrato '{contrato_id}' não encontrado.", type_suffix="contrato-nao-encontrado")
    return contrato


async def criar(db: AsyncSession, dados: ContratoCreatePayload) -> Contrato:
    if not dados.art_fiscalizacao.strip():
        raise DomainError(
            "ART de Fiscalização é obrigatória (RN-09).",
            type_suffix="art-fiscalizacao-obrigatoria",
            title="Contrato inválido",
        )
    await _validar_referencias(db, dados)
    return await contrato_repository.create_with_executores_nbrs(db, dados)


async def atualizar(db: AsyncSession, contrato_id: uuid.UUID, dados: ContratoUpdatePayload) -> Contrato:
    if not dados.art_fiscalizacao.strip():
        raise DomainError(
            "ART de Fiscalização é obrigatória (RN-09).",
            type_suffix="art-fiscalizacao-obrigatoria",
            title="Contrato inválido",
        )
    contrato = await obter_por_id(db, contrato_id)
    await _validar_referencias(db, dados)
    return await contrato_repository.update_with_executores_nbrs(db, contrato, dados)
