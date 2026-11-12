"""`GET /api/v1/ia/uso` — consumo e custo da IA por dia e modelo (BL-34, R-10). Só `auditor`."""
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auditor
from app.core.database import get_db
from app.core.errors import DomainError
from app.models import ChamadaIA, Usuario

router = APIRouter(prefix="/api/v1/ia", tags=["ia"])

_JANELA_PADRAO_DIAS = 30


class UsoIADia(BaseModel):
    dia: date
    modelo: str | None
    chamadas: int
    chamadas_api: int
    chamadas_cache_local: int
    erros: int
    tokens_prompt: int
    tokens_cache_hit: int
    tokens_cache_miss: int
    tokens_saida: int
    # % dos tokens de entrada que a DeepSeek serviu do próprio cache (None sem tokens de entrada).
    pct_tokens_cache_hit: float | None
    custo_estimado_usd: Decimal | None


class UsoIARead(BaseModel):
    de: date
    ate: date
    dias: list[UsoIADia]


@router.get("/uso", response_model=UsoIARead)
async def uso_ia(
    de: date | None = Query(default=None, description="Início (inclusive); padrão: 30 dias atrás."),
    ate: date | None = Query(default=None, description="Fim (inclusive); padrão: hoje (UTC)."),
    db: AsyncSession = Depends(get_db),
    _usuario: Usuario = Depends(require_auditor),
) -> UsoIARead:
    hoje = datetime.now(UTC).date()
    ate = ate or hoje
    de = de or (ate - timedelta(days=_JANELA_PADRAO_DIAS))
    if de > ate:
        raise DomainError(
            "O início do período não pode ser posterior ao fim.",
            type_suffix="periodo-invalido", title="Período inválido",
        )
    inicio = datetime.combine(de, time.min, tzinfo=UTC)
    fim = datetime.combine(ate + timedelta(days=1), time.min, tzinfo=UTC)
    dia = cast(func.timezone("UTC", ChamadaIA.criado_em), Date).label("dia")

    def _soma(coluna):
        return func.coalesce(func.sum(coluna), 0)

    consulta = (
        select(
            dia,
            ChamadaIA.modelo,
            func.count().label("chamadas"),
            func.count().filter(ChamadaIA.origem == "api").label("chamadas_api"),
            func.count().filter(ChamadaIA.origem == "cache_local").label("chamadas_cache_local"),
            func.count().filter(ChamadaIA.sucesso.is_(False)).label("erros"),
            _soma(ChamadaIA.tokens_prompt).label("tokens_prompt"),
            _soma(ChamadaIA.tokens_cache_hit).label("tokens_cache_hit"),
            _soma(ChamadaIA.tokens_cache_miss).label("tokens_cache_miss"),
            _soma(ChamadaIA.tokens_saida).label("tokens_saida"),
            func.sum(ChamadaIA.custo_estimado_usd).label("custo"),
        )
        .where(ChamadaIA.criado_em >= inicio, ChamadaIA.criado_em < fim)
        .group_by(dia, ChamadaIA.modelo)
        .order_by(dia, ChamadaIA.modelo)
    )
    linhas = (await db.execute(consulta)).all()
    dias = []
    for r in linhas:
        entrada = r.tokens_cache_hit + r.tokens_cache_miss
        dias.append(
            UsoIADia(
                dia=r.dia, modelo=r.modelo, chamadas=r.chamadas, chamadas_api=r.chamadas_api,
                chamadas_cache_local=r.chamadas_cache_local, erros=r.erros,
                tokens_prompt=r.tokens_prompt, tokens_cache_hit=r.tokens_cache_hit,
                tokens_cache_miss=r.tokens_cache_miss, tokens_saida=r.tokens_saida,
                pct_tokens_cache_hit=round(100 * r.tokens_cache_hit / entrada, 2) if entrada else None,
                custo_estimado_usd=r.custo,
            )
        )
    return UsoIARead(de=de, ate=ate, dias=dias)
