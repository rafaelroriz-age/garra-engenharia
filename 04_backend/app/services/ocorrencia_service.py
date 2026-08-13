"""Service Layer de `Ocorrencia` (BL-14, RF-04, RN-03, RN-05, RN-10)."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError, NotFoundError
from app.models import Ocorrencia
from app.repositories import ocorrencia_repository
from app.schemas.ocorrencia import OcorrenciaCreate


async def obter_por_id(db: AsyncSession, ocorrencia_id: uuid.UUID) -> Ocorrencia:
    ocorrencia = await ocorrencia_repository.get_by_id(db, ocorrencia_id)
    if ocorrencia is None:
        raise NotFoundError(f"Ocorrência '{ocorrencia_id}' não encontrada.", type_suffix="ocorrencia-nao-encontrada")
    return ocorrencia


async def listar_por_inspecao(
    db: AsyncSession,
    *,
    inspecao_id: uuid.UUID,
    sistema_id: str | None = None,
    grau_risco: str | None = None,
) -> list[Ocorrencia]:
    return await ocorrencia_repository.list_by_inspecao(
        db,
        inspecao_id=inspecao_id,
        sistema_id=sistema_id,
        grau_risco=grau_risco,
    )


async def listar_todas_por_inspecao(db: AsyncSession, *, inspecao_id: uuid.UUID) -> list[Ocorrencia]:
    return await ocorrencia_repository.list_all_by_inspecao(db, inspecao_id=inspecao_id)


async def criar(db: AsyncSession, *, inspecao_id: uuid.UUID, dados: OcorrenciaCreate) -> Ocorrencia:
    _validar_payload(dados)
    return await ocorrencia_repository.create(db, inspecao_id=inspecao_id, dados=dados)


async def atualizar(db: AsyncSession, ocorrencia_id: uuid.UUID, dados: OcorrenciaCreate) -> Ocorrencia:
    _validar_payload(dados)
    ocorrencia = await obter_por_id(db, ocorrencia_id)
    return await ocorrencia_repository.update(db, ocorrencia, dados)


async def remover(db: AsyncSession, ocorrencia_id: uuid.UUID) -> None:
    ocorrencia = await obter_por_id(db, ocorrencia_id)
    await ocorrencia_repository.delete(db, ocorrencia)


def _validar_payload(dados: OcorrenciaCreate) -> None:
    if not dados.sistema_id:
        raise DomainError("Sistema predial é obrigatório.", type_suffix="ocorrencia-sistema-obrigatorio")
    if not dados.situacao:
        raise DomainError("Situação é obrigatória.", type_suffix="ocorrencia-situacao-obrigatoria")
    if not dados.classificacao:
        raise DomainError("Classificação é obrigatória.", type_suffix="ocorrencia-classificacao-obrigatoria")
    if dados.classificacao in {"ANOMALIA", "ANOMALIA_FALHA"} and not dados.tipo_anomalia:
        raise DomainError("Tipo de anomalia é obrigatório para esta classificação.", type_suffix="ocorrencia-tipo-anomalia-obrigatorio")
    if dados.classificacao in {"FALHA", "ANOMALIA_FALHA"} and not dados.tipo_falha:
        raise DomainError("Tipo de falha é obrigatório para esta classificação.", type_suffix="ocorrencia-tipo-falha-obrigatorio")
    if dados.grau_risco not in {"MINIMO", "MEDIO", "CRITICO"}:
        raise DomainError("Grau de risco inválido.", type_suffix="ocorrencia-grau-risco-invalido")
    # RN-05: Prioridade deve estar entre 0 (sem prioridade definida) e 5.
    if dados.prioridade is not None and not (0 <= dados.prioridade <= 5):
        raise DomainError("Prioridade deve estar entre 0 e 5.", type_suffix="ocorrencia-prioridade-invalida")
