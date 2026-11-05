"""Service Layer de `Visita`, `VisitaMaoObra` e `VisitaMedicao` (BL-10, RF-03, RN-01, RN-02).

Regras de domínio de DEC-38: visita só em inspeção RFO (A); uma visita por dia e `seq_numero`
único por inspeção, com lock da inspeção e UNIQUE no banco (B); itens de equipe/medição
consultáveis, corrigíveis e removíveis (E). Erros em RFC 7807 via `DomainError` (ADR-07).
"""
import uuid
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models import Visita, VisitaMaoObra, VisitaMedicao
from app.repositories import visita_repository
from app.schemas.visita import VisitaCreatePayload, VisitaUpdatePayload
from app.schemas.visita_mao_obra import VisitaMaoObraCreatePayload
from app.schemas.visita_medicao import VisitaMedicaoCreatePayload
from app.services import inspecao_service

# Tipo de Inspeção que admite Visitas (RF-03: "Registro de Visitas para RFO"). `Inspecao.tipo` é
# texto livre hoje (há dados com "ltip" minúsculo), então a comparação ignora caixa e espaços.
TIPO_INSPECAO_COM_VISITAS = "RFO"


def _data_duplicada(visita_data: date) -> ConflictError:
    return ConflictError(
        f"Já existe uma visita nesta inspeção na data {visita_data.isoformat()} "
        "(RN-01: uma visita por dia de obra acompanhado).",
        type_suffix="visita-data-duplicada",
    )


def _conflito_de_unicidade(exc: IntegrityError, visita_data: date) -> ConflictError:
    """Traduz a violação de UNIQUE (corrida que escapou do lock) em 409 em vez de 500."""
    if "uq_visitas_inspecao_id_data" in str(exc.orig):
        return _data_duplicada(visita_data)
    return ConflictError(
        "Outra visita foi registrada ao mesmo tempo nesta inspeção; tente novamente.",
        type_suffix="visita-seq-numero-concorrente",
    )


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
    inspecao = await inspecao_service.obter_por_id(db, inspecao_id)  # 404 se não existe
    if (inspecao.tipo or "").strip().upper() != TIPO_INSPECAO_COM_VISITAS:
        raise ConflictError(
            f"Visitas só podem ser registradas em inspeção do tipo RFO (esta é '{inspecao.tipo}').",
            type_suffix="visita-exige-inspecao-rfo",
        )
    await visita_repository.bloquear_inspecao(db, inspecao_id)
    if await visita_repository.existe_visita_na_data(db, inspecao_id, dados.data):
        await db.rollback()
        raise _data_duplicada(dados.data)
    try:
        return await visita_repository.create_visita(db, inspecao_id, dados, criado_por_id=criado_por_id)
    except IntegrityError as exc:
        await db.rollback()
        raise _conflito_de_unicidade(exc, dados.data) from exc


async def atualizar_visita(db: AsyncSession, visita_id: uuid.UUID, dados: VisitaUpdatePayload) -> Visita:
    visita = await obter_por_id(db, visita_id)
    data_alvo = dados.data if "data" in dados.model_fields_set else visita.data
    if data_alvo != visita.data:
        await visita_repository.bloquear_inspecao(db, visita.inspecao_id)
        if await visita_repository.existe_visita_na_data(db, visita.inspecao_id, data_alvo, exceto_id=visita.id):
            await db.rollback()
            raise _data_duplicada(data_alvo)
    try:
        return await visita_repository.update_visita(db, visita, dados)
    except IntegrityError as exc:
        await db.rollback()
        raise _conflito_de_unicidade(exc, data_alvo) from exc


# ---------------------------------------------------------------- Mão de obra

async def listar_mao_obra(db: AsyncSession, visita_id: uuid.UUID) -> list[VisitaMaoObra]:
    await obter_por_id(db, visita_id)
    return await visita_repository.list_mao_obra(db, visita_id)


async def obter_mao_obra(db: AsyncSession, visita_id: uuid.UUID, item_id: uuid.UUID) -> VisitaMaoObra:
    await obter_por_id(db, visita_id)
    registro = await visita_repository.get_mao_obra(db, visita_id, item_id)
    if registro is None:
        raise NotFoundError(
            f"Mão de obra '{item_id}' não encontrada na visita '{visita_id}'.",
            type_suffix="mao-obra-nao-encontrada",
        )
    return registro


async def adicionar_mao_obra(
    db: AsyncSession, visita_id: uuid.UUID, dados: VisitaMaoObraCreatePayload
) -> VisitaMaoObra:
    await obter_por_id(db, visita_id)
    return await visita_repository.add_mao_obra(db, visita_id, dados)


async def atualizar_mao_obra(
    db: AsyncSession, visita_id: uuid.UUID, item_id: uuid.UUID, dados: VisitaMaoObraCreatePayload
) -> VisitaMaoObra:
    registro = await obter_mao_obra(db, visita_id, item_id)
    return await visita_repository.update_mao_obra(db, registro, dados)


async def remover_mao_obra(db: AsyncSession, visita_id: uuid.UUID, item_id: uuid.UUID) -> None:
    registro = await obter_mao_obra(db, visita_id, item_id)
    await visita_repository.delete_item(db, registro)


# ---------------------------------------------------------------- Medições

async def listar_medicoes(db: AsyncSession, visita_id: uuid.UUID) -> list[VisitaMedicao]:
    await obter_por_id(db, visita_id)
    return await visita_repository.list_medicoes(db, visita_id)


async def obter_medicao(db: AsyncSession, visita_id: uuid.UUID, item_id: uuid.UUID) -> VisitaMedicao:
    await obter_por_id(db, visita_id)
    registro = await visita_repository.get_medicao(db, visita_id, item_id)
    if registro is None:
        raise NotFoundError(
            f"Medição '{item_id}' não encontrada na visita '{visita_id}'.",
            type_suffix="medicao-nao-encontrada",
        )
    return registro


async def adicionar_medicao(
    db: AsyncSession, visita_id: uuid.UUID, dados: VisitaMedicaoCreatePayload
) -> VisitaMedicao:
    await obter_por_id(db, visita_id)
    return await visita_repository.add_medicao(db, visita_id, dados)


async def atualizar_medicao(
    db: AsyncSession, visita_id: uuid.UUID, item_id: uuid.UUID, dados: VisitaMedicaoCreatePayload
) -> VisitaMedicao:
    registro = await obter_medicao(db, visita_id, item_id)
    return await visita_repository.update_medicao(db, registro, dados)


async def remover_medicao(db: AsyncSession, visita_id: uuid.UUID, item_id: uuid.UUID) -> None:
    registro = await obter_medicao(db, visita_id, item_id)
    await visita_repository.delete_item(db, registro)
