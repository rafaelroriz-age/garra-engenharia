"""Endpoints de Dados Mestre / Gabarito (BL-05, RF-10).

Ver `00_docs/arquitetura.md` Seção 4 ("Dados Mestre"):
- `GET /api/v1/sistemas-prediais`
- `GET /api/v1/gabarito/tipos-anomalia`
- `GET /api/v1/gabarito/tipos-falha`
- `GET /api/v1/gabarito/localizacoes`

Todos read-only: o gabarito é populado pelo seed (`app.scripts.seed_gabarito`),
não por estes endpoints. Sem parâmetros de entrada a validar.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Localizacao, SistemaPredial, TipoAnomalia, TipoFalha
from app.schemas import (
    LocalizacaoRead,
    SistemaPredialComSubsistemas,
    TipoAnomaliaRead,
    TipoFalhaRead,
)

router = APIRouter(prefix="/api/v1", tags=["dados-mestre"])


@router.get("/sistemas-prediais", response_model=list[SistemaPredialComSubsistemas])
async def listar_sistemas_prediais(
    db: AsyncSession = Depends(get_db),
) -> list[SistemaPredial]:
    """Lista os sistemas prediais do gabarito, cada um com seus subsistemas (RF-10)."""
    result = await db.execute(
        select(SistemaPredial)
        .options(selectinload(SistemaPredial.subsistemas))
        .order_by(SistemaPredial.ordem)
    )
    return list(result.scalars().all())


@router.get("/gabarito/tipos-anomalia", response_model=list[TipoAnomaliaRead])
async def listar_tipos_anomalia(db: AsyncSession = Depends(get_db)) -> list[TipoAnomalia]:
    """Lista os tipos de anomalia do gabarito (RF-10)."""
    result = await db.execute(select(TipoAnomalia).order_by(TipoAnomalia.ordem))
    return list(result.scalars().all())


@router.get("/gabarito/tipos-falha", response_model=list[TipoFalhaRead])
async def listar_tipos_falha(db: AsyncSession = Depends(get_db)) -> list[TipoFalha]:
    """Lista os tipos de falha do gabarito (RF-10)."""
    result = await db.execute(select(TipoFalha).order_by(TipoFalha.ordem))
    return list(result.scalars().all())


@router.get("/gabarito/localizacoes", response_model=list[LocalizacaoRead])
async def listar_localizacoes(db: AsyncSession = Depends(get_db)) -> list[Localizacao]:
    """Lista as localizações padrão do gabarito (RF-10)."""
    result = await db.execute(select(Localizacao).order_by(Localizacao.ordem))
    return list(result.scalars().all())
