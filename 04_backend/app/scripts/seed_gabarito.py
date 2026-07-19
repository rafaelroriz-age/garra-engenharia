"""Seed do gabarito de sistemas prediais/subsistemas/tipos de anomalia/falha/localizações (BL-05, RF-10).

Popula as tabelas `sistemas_prediais`, `subsistemas`, `tipos_anomalia`,
`tipos_falha` e `localizacoes` a partir do gabarito extraído de
`00_docs/convertidos/RFO_INSPECAO.md` (ver `app.scripts.rfo_gabarito_parser`).

Idempotente: cada execução verifica se o registro (por `nome`, e por
`sistema_id` + `nome` no caso de Subsistema) já existe antes de inserir, então
pode ser rodado múltiplas vezes sem duplicar dados.

Uso:
    cd 04_backend
    python -m app.scripts.seed_gabarito
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import Localizacao, SistemaPredial, Subsistema, TipoAnomalia, TipoFalha
from app.scripts.rfo_gabarito_parser import build_gabarito

logger = logging.getLogger(__name__)


async def _upsert_dominio_simples(
    session: AsyncSession, modelo: type, nome: str, ordem: int
) -> None:
    """Insere um registro de dado mestre simples (`id`, `nome`, `ordem`) se ainda não existir."""
    existente = await session.execute(select(modelo).where(modelo.nome == nome))
    if existente.scalar_one_or_none() is not None:
        return
    session.add(modelo(nome=nome, ordem=ordem))


async def _upsert_sistema(session: AsyncSession, nome: str, ordem: int) -> SistemaPredial:
    existente = await session.execute(select(SistemaPredial).where(SistemaPredial.nome == nome))
    sistema = existente.scalar_one_or_none()
    if sistema is None:
        sistema = SistemaPredial(nome=nome, ordem=ordem)
        session.add(sistema)
        await session.flush()
    return sistema


async def _upsert_subsistema(
    session: AsyncSession, sistema: SistemaPredial, nome: str, ordem: int
) -> None:
    existente = await session.execute(
        select(Subsistema).where(Subsistema.sistema_id == sistema.id, Subsistema.nome == nome)
    )
    if existente.scalar_one_or_none() is not None:
        return
    session.add(Subsistema(sistema_id=sistema.id, nome=nome, ordem=ordem))


async def seed_gabarito(session: AsyncSession) -> dict[str, int]:
    """Popula o gabarito de dados mestre e retorna um resumo de contagens inseridas/lidas."""
    gabarito = build_gabarito()
    sistemas: list[str] = gabarito["sistemas"]  # type: ignore[assignment]
    subsistemas_por_sistema: dict[str, list[str]] = gabarito["subsistemas_por_sistema"]  # type: ignore[assignment]
    tipos_anomalia: list[str] = gabarito["tipos_anomalia"]  # type: ignore[assignment]
    tipos_falha: list[str] = gabarito["tipos_falha"]  # type: ignore[assignment]
    localizacoes: list[str] = gabarito["localizacoes"]  # type: ignore[assignment]

    total_subsistemas = 0
    for ordem_sistema, nome_sistema in enumerate(sistemas, start=1):
        sistema = await _upsert_sistema(session, nome_sistema, ordem_sistema)
        subsistemas = subsistemas_por_sistema.get(nome_sistema, [])
        for ordem_sub, nome_sub in enumerate(subsistemas, start=1):
            await _upsert_subsistema(session, sistema, nome_sub, ordem_sub)
            total_subsistemas += 1

    for ordem, nome in enumerate(tipos_anomalia, start=1):
        await _upsert_dominio_simples(session, TipoAnomalia, nome, ordem)
    for ordem, nome in enumerate(tipos_falha, start=1):
        await _upsert_dominio_simples(session, TipoFalha, nome, ordem)
    for ordem, nome in enumerate(localizacoes, start=1):
        await _upsert_dominio_simples(session, Localizacao, nome, ordem)

    await session.commit()

    return {
        "sistemas_prediais": len(sistemas),
        "subsistemas": total_subsistemas,
        "tipos_anomalia": len(tipos_anomalia),
        "tipos_falha": len(tipos_falha),
        "localizacoes": len(localizacoes),
    }


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    async with AsyncSessionLocal() as session:
        resumo = await seed_gabarito(session)
    logger.info("Seed do gabarito concluído: %s", resumo)


if __name__ == "__main__":
    asyncio.run(main())
