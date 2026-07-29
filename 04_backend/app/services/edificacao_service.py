"""Service Layer de `Edificacao` (BL-08, RF-01).

Concentra as regras de negócio do CRUD de Edificações; o repository
(`app.repositories.edificacao_repository`) só executa queries.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.models import Contrato, Edificacao, Inspecao, Ocorrencia
from app.repositories import edificacao_repository
from app.schemas.dashboard import (
    DashboardConformidadePorSistema,
    DashboardEdificacaoRead,
    DashboardGrauRiscoPorSistema,
    DashboardGravidadePorSubsistema,
)
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


async def obter_dashboard(db: AsyncSession, edificacao_id: uuid.UUID) -> DashboardEdificacaoRead:
    edificacao = await obter_por_id(db, edificacao_id)

    stmt = (
        select(Ocorrencia)
        .join(Inspecao, Ocorrencia.inspecao_id == Inspecao.id)
        .join(Contrato, Inspecao.contrato_id == Contrato.id)
        .where(Contrato.edificacao_id == edificacao_id)
        .options(selectinload(Ocorrencia.sistema), selectinload(Ocorrencia.subsistema))
    )
    result = await db.execute(stmt)
    ocorrencias = list(result.scalars().all())

    conformidade_por_sistema: dict[uuid.UUID, dict[str, int]] = {}
    grau_risco_por_sistema: dict[uuid.UUID, dict[str, int]] = {}
    gravidade_por_subsistema: dict[uuid.UUID, dict[str, object]] = {}

    for ocorrencia in ocorrencias:
        sistema_id = ocorrencia.sistema_id
        if sistema_id not in conformidade_por_sistema:
            conformidade_por_sistema[sistema_id] = {"conforme": 0, "nao_conforme": 0, "total": 0}
            grau_risco_por_sistema[sistema_id] = {"MINIMO": 0, "MEDIO": 0, "CRITICO": 0}

        item_conformidade = conformidade_por_sistema[sistema_id]
        item_conformidade["total"] += 1
        if ocorrencia.situacao == "CONFORME":
            item_conformidade["conforme"] += 1
        else:
            item_conformidade["nao_conforme"] += 1

        if ocorrencia.grau_risco in grau_risco_por_sistema[sistema_id]:
            grau_risco_por_sistema[sistema_id][ocorrencia.grau_risco] += 1

        if ocorrencia.subsistema_id is not None:
            subsistema_id = ocorrencia.subsistema_id
            if subsistema_id not in gravidade_por_subsistema:
                gravidade_por_subsistema[subsistema_id] = {
                    "subsistema_id": subsistema_id,
                    "subsistema_nome": ocorrencia.subsistema.nome if ocorrencia.subsistema else "—",
                    "sistema_nome": ocorrencia.sistema.nome if ocorrencia.sistema else None,
                    "total": 0,
                    "somatorio": 0.0,
                }
            item_gravidade = gravidade_por_subsistema[subsistema_id]
            item_gravidade["total"] += 1
            item_gravidade["somatorio"] += float(ocorrencia.gut_gravidade or 0.0)

    return DashboardEdificacaoRead(
        edificacao_id=edificacao.id,
        edificacao_nome=edificacao.nome,
        conformidade_por_sistema=[
            DashboardConformidadePorSistema(
                sistema_id=sistema_id,
                sistema_nome=(ocorrencia.sistema.nome if (ocorrencia := next((o for o in ocorrencias if o.sistema_id == sistema_id), None)) else None) or "—",
                conforme=dados["conforme"],
                nao_conforme=dados["nao_conforme"],
                total=dados["total"],
            )
            for sistema_id, dados in conformidade_por_sistema.items()
        ],
        grau_risco_por_sistema=[
            DashboardGrauRiscoPorSistema(
                sistema_id=sistema_id,
                sistema_nome=(ocorrencia.sistema.nome if (ocorrencia := next((o for o in ocorrencias if o.sistema_id == sistema_id), None)) else None) or "—",
                minimo=dados["MINIMO"],
                medio=dados["MEDIO"],
                critico=dados["CRITICO"],
            )
            for sistema_id, dados in grau_risco_por_sistema.items()
        ],
        gravidade_por_subsistema=[
            DashboardGravidadePorSubsistema(
                subsistema_id=dados["subsistema_id"],
                subsistema_nome=dados["subsistema_nome"],
                sistema_nome=dados["sistema_nome"],
                media_gravidade=(
                    float(dados["somatorio"]) / float(dados["total"])
                    if int(dados["total"]) > 0
                    else 0.0
                ),
            )
            for dados in gravidade_por_subsistema.values()
        ],
    )
