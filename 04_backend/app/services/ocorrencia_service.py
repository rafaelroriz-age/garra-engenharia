"""Service Layer de `Ocorrencia` (BL-14/BL-15, RF-04, RN-03, RN-04, RN-05, RN-10)."""
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError, NotFoundError
from app.models import Ocorrencia
from app.repositories import ocorrencia_repository
from app.schemas.ocorrencia import OcorrenciaCreate

# RN-04 (DEC-29): mapeamento Grau de Risco CMM → Prioridade sugerida.
_PRIORIDADE_POR_GRAU = {"CRITICO": 5, "MEDIO": 3, "MINIMO": 1}


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


async def criar(
    db: AsyncSession,
    *,
    inspecao_id: uuid.UUID,
    dados: OcorrenciaCreate,
    criado_por_id: uuid.UUID | None = None,
) -> Ocorrencia:
    _validar_payload(dados)
    prioridade, prioridade_sugerida, ajustado_por_id, ajustado_em = _resolver_prioridade(dados, criado_por_id)
    return await ocorrencia_repository.create(
        db,
        inspecao_id=inspecao_id,
        dados=dados,
        criado_por_id=criado_por_id,
        prioridade=prioridade,
        prioridade_sugerida=prioridade_sugerida,
        prioridade_ajustada_por_id=ajustado_por_id,
        prioridade_ajustada_em=ajustado_em,
    )


async def atualizar(
    db: AsyncSession,
    ocorrencia_id: uuid.UUID,
    dados: OcorrenciaCreate,
    usuario_id: uuid.UUID | None = None,
) -> Ocorrencia:
    _validar_payload(dados)
    ocorrencia = await obter_por_id(db, ocorrencia_id)
    prioridade, prioridade_sugerida, ajustado_por_id, ajustado_em = _resolver_prioridade(dados, usuario_id)
    return await ocorrencia_repository.update(
        db,
        ocorrencia,
        dados,
        prioridade=prioridade,
        prioridade_sugerida=prioridade_sugerida,
        prioridade_ajustada_por_id=ajustado_por_id,
        prioridade_ajustada_em=ajustado_em,
    )


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
    # RN-05: Prioridade deve estar entre 0 (não aplicável) e 5.
    if dados.prioridade is not None and not (0 <= dados.prioridade <= 5):
        raise DomainError("Prioridade deve estar entre 0 e 5.", type_suffix="ocorrencia-prioridade-invalida")


def _prioridade_sugerida(dados: OcorrenciaCreate) -> int:
    """Deriva a prioridade sugerida a partir do Grau de Risco CMM (RN-04/DEC-29).

    "Prioridade 0" significa "não aplicável" — ocorrência Conforme ou sistema
    registrado como "Não se Aplica" (RN-10). Nos demais casos, segue o mapeamento
    Crítico=5, Médio=3, Mínimo=1.
    """
    if dados.situacao == "CONFORME" or dados.classificacao == "NAO_SE_APLICA":
        return 0
    return _PRIORIDADE_POR_GRAU[dados.grau_risco]


def _resolver_prioridade(
    dados: OcorrenciaCreate,
    usuario_id: uuid.UUID | None,
) -> tuple[int, int, uuid.UUID | None, datetime | None]:
    """Resolve a prioridade efetiva e o rastreio da sobrescrita explícita (RN-04).

    Retorna `(prioridade, prioridade_sugerida, prioridade_ajustada_por_id,
    prioridade_ajustada_em)`. Quando a prioridade não é informada, assume a
    sugestão derivada do Grau de Risco; quando difere da sugestão, registra a
    autoria e o instante do ajuste.
    """
    sugerida = _prioridade_sugerida(dados)
    efetiva = dados.prioridade if dados.prioridade is not None else sugerida
    if efetiva != sugerida:
        return efetiva, sugerida, usuario_id, datetime.now(UTC)
    return efetiva, sugerida, None, None
