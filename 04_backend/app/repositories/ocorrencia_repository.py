"""Repository de `Ocorrencia` (BL-14, RF-04, RN-03, RN-05, RN-10)."""
import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Foto, Inspecao, Ocorrencia, SistemaPredial, Subsistema
from app.schemas.ocorrencia import OcorrenciaCreate


_DETALHE_OPTIONS = (
    selectinload(Ocorrencia.fotos),
    selectinload(Ocorrencia.sistema),
    selectinload(Ocorrencia.subsistema),
)


async def get_by_id(db: AsyncSession, ocorrencia_id: uuid.UUID) -> Ocorrencia | None:
    result = await db.execute(select(Ocorrencia).options(*_DETALHE_OPTIONS).where(Ocorrencia.id == ocorrencia_id))
    return result.scalar_one_or_none()


async def list_by_inspecao(
    db: AsyncSession,
    *,
    inspecao_id: uuid.UUID,
    sistema_id: str | None = None,
    grau_risco: str | None = None,
) -> list[Ocorrencia]:
    filtros = [Ocorrencia.inspecao_id == inspecao_id]
    if sistema_id:
        filtros.append(Ocorrencia.sistema_id == uuid.UUID(sistema_id))
    if grau_risco:
        filtros.append(Ocorrencia.grau_risco == grau_risco)

    result = await db.execute(
        select(Ocorrencia)
        .options(*_DETALHE_OPTIONS)
        .where(and_(*filtros))
        .order_by(Ocorrencia.seq_numero)
    )
    return list(result.scalars().all())


async def list_all_by_inspecao(db: AsyncSession, *, inspecao_id: uuid.UUID) -> list[Ocorrencia]:
    result = await db.execute(
        select(Ocorrencia)
        .options(*_DETALHE_OPTIONS)
        .where(Ocorrencia.inspecao_id == inspecao_id)
        .order_by(Ocorrencia.seq_numero)
    )
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    *,
    inspecao_id: uuid.UUID,
    dados: OcorrenciaCreate,
    criado_por_id: uuid.UUID | None = None,
) -> Ocorrencia:
    ocorrencia = Ocorrencia(
        inspecao_id=inspecao_id,
        sistema_id=dados.sistema_id,
        subsistema_id=dados.subsistema_id,
        localizacao=dados.localizacao,
        situacao=dados.situacao,
        classificacao=dados.classificacao,
        tipo_anomalia=dados.tipo_anomalia,
        tipo_falha=dados.tipo_falha,
        grau_risco=dados.grau_risco,
        prioridade=dados.prioridade,
        descricao=dados.descricao,
        gut_gravidade=dados.gut_gravidade,
        gut_urgencia=dados.gut_urgencia,
        gut_tendencia=dados.gut_tendencia,
        seq_numero=await _proximo_seq_numero(db, inspecao_id),
        criado_por_id=criado_por_id,
    )
    db.add(ocorrencia)
    await db.commit()
    await db.refresh(ocorrencia)
    return ocorrencia


async def update(db: AsyncSession, ocorrencia: Ocorrencia, dados: OcorrenciaCreate) -> Ocorrencia:
    for campo, valor in dados.model_dump().items():
        setattr(ocorrencia, campo, valor)
    await db.commit()
    await db.refresh(ocorrencia)
    return ocorrencia


async def delete(db: AsyncSession, ocorrencia: Ocorrencia) -> None:
    await db.delete(ocorrencia)
    await db.commit()


async def _proximo_seq_numero(db: AsyncSession, inspecao_id: uuid.UUID) -> int:
    maior_atual = (
        await db.execute(select(func.max(Ocorrencia.seq_numero)).where(Ocorrencia.inspecao_id == inspecao_id))
    ).scalar_one()
    return (maior_atual or 0) + 1
