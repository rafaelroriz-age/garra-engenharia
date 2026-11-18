"""Expurgo da coluna `resposta` de `chamadas_ia` vencida (DEC-52, BL-34, R-10).

`resposta` guarda a legenda saneada para servir de cache local. Ela é dado derivado de fotos de
clientes, então precisa de retenção: linhas com `criado_em` anterior a `agora - TTL` têm só essa
coluna anulada (`resposta = NULL`). Não apaga linhas e não altera tokens, custo, latência, origem,
chave de cache, modelo ou qualquer outra coluna.

Regras:
- Padrão é dry-run: conta e imprime quantas linhas seriam anuladas, sem escrever. Só `--aplicar` grava.
- TTL: `--ttl-horas` (>= 1) tem prioridade. Sem a flag, usa `LEGENDA_IA_CACHE_TTL_H`. Se essa
  variável for `0` (cache desligado), o script usa o padrão de 720 h e avisa, em vez de anular tudo
  por engano. Escolha documentada em 00_docs/backlog-auto/ia-retencao-chamadas.md.
- Idempotente: uma segunda execução com o mesmo TTL não encontra linhas vencidas com `resposta`.
- Cache local (`buscar_em_cache`) já filtra `resposta IS NOT NULL`: linha expurgada é miss, nunca acerto.

Uso (a partir de `04_backend/`):
    python -m app.scripts.limpar_chamadas_ia                 # dry-run, TTL da configuração
    python -m app.scripts.limpar_chamadas_ia --ttl-horas 168 # dry-run com TTL de 7 dias
    python -m app.scripts.limpar_chamadas_ia --aplicar       # grava o expurgo
"""
import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, null, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models import ChamadaIA
from app.services.legenda_ia.telemetria import tem_resposta

TTL_PADRAO_H = 720


def _ttl_efetivo(ttl_horas_arg: int | None, ttl_config: int) -> tuple[int, str | None]:
    """Devolve (ttl em horas, aviso ou None). Flag tem prioridade; config 0 cai no padrão de 720 h."""
    if ttl_horas_arg is not None:
        return ttl_horas_arg, None
    if ttl_config <= 0:
        return TTL_PADRAO_H, (
            f"LEGENDA_IA_CACHE_TTL_H={ttl_config} (cache desligado): usando o padrão de {TTL_PADRAO_H} h. "
            "Para outro prazo, passe --ttl-horas."
        )
    return ttl_config, None


def _filtro_vencidas(limite: datetime):
    return (tem_resposta(), ChamadaIA.criado_em < limite)


async def expurgar(db: AsyncSession, ttl_h: int, aplicar: bool, agora: datetime | None = None) -> int:
    """Conta (dry-run) ou anula `resposta` das linhas vencidas. Devolve a quantidade afetada/prevista."""
    limite = (agora or datetime.now(UTC)) - timedelta(hours=ttl_h)
    filtro = _filtro_vencidas(limite)
    if not aplicar:
        return (await db.execute(select(func.count()).select_from(ChamadaIA).where(*filtro))).scalar_one()
    resultado = await db.execute(
        update(ChamadaIA)
        .where(*filtro)
        .values(resposta=null())  # SQL NULL, não JSON null: o filtro de tem_resposta() deixa de casar
        .execution_options(synchronize_session=False)
    )
    await db.commit()
    return resultado.rowcount


async def _executar(args: argparse.Namespace) -> int:
    settings = get_settings()
    ttl_h, aviso = _ttl_efetivo(args.ttl_horas, settings.legenda_ia_cache_ttl_h)
    if aviso:
        print(f"AVISO: {aviso}", file=sys.stderr)
    engine = create_async_engine(settings.database_url, poolclass=NullPool, future=True)
    try:
        async with async_sessionmaker(bind=engine, expire_on_commit=False)() as db:
            n = await expurgar(db, ttl_h, args.aplicar)
    finally:
        await engine.dispose()
    if args.aplicar:
        print(f"Aplicado: resposta anulada em {n} linha(s) com TTL de {ttl_h} h.")
    else:
        print(f"Dry-run: {n} linha(s) teriam resposta anulada com TTL de {ttl_h} h. Nada foi gravado (use --aplicar).")
    return 0


def _ttl_positivo(valor: str) -> int:
    n = int(valor)
    if n < 1:
        raise argparse.ArgumentTypeError("--ttl-horas deve ser >= 1")
    return n


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Anula resposta de chamadas_ia vencida (DEC-52). Dry-run por padrão.")
    p.add_argument("--aplicar", action="store_true", help="grava o UPDATE (sem isso, só conta)")
    p.add_argument("--ttl-horas", type=_ttl_positivo, help="prazo em horas (>= 1); sobrescreve LEGENDA_IA_CACHE_TTL_H")
    return asyncio.run(_executar(p.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
