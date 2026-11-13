"""Relatório de objetos órfãos do storage — DRY-RUN (DEC-44, itens 1-3).

Lista objetos do bucket sob `--prefixo` que NÃO estão vinculados a nenhuma
`Foto.storage_key` no banco e que têm idade maior que `--idade-minima-horas`.

SOMENTE LEITURA: este script não apaga nada e não tem flag de exclusão. Apagar
exige aprovação manual da lista (DEC-44 item 3) e fica para tarefa futura.

Uso:
    cd 04_backend
    python -m app.scripts.relatorio_orfaos [--idade-minima-horas 24] [--prefixo fotos/]
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

IDADE_MINIMA_HORAS_PADRAO = 24
PREFIXO_PADRAO = "fotos/"


async def consultar_chaves_vinculadas() -> set[str]:
    """Chaves de foto registradas no banco (`Foto.storage_key`)."""
    from app.core.database import AsyncSessionLocal
    from app.models import Foto

    async with AsyncSessionLocal() as db:
        rows = await db.execute(select(Foto.storage_key))
        return {k for (k,) in rows.all() if k}


def calcular_orfaos(
    objetos: Iterable[tuple[str, datetime]],
    chaves_vinculadas: Iterable[str],
    idade_minima_horas: float = IDADE_MINIMA_HORAS_PADRAO,
    agora: datetime | None = None,
) -> list[tuple[str, datetime, float]]:
    """Órfãos com idade > limite: lista de `(chave, last_modified, idade_em_horas)`."""
    agora = agora or datetime.now(UTC)
    vinculadas = set(chaves_vinculadas)
    limite = timedelta(hours=idade_minima_horas)
    resultado = []
    for chave, modificado in objetos:
        if modificado.tzinfo is None:
            modificado = modificado.replace(tzinfo=UTC)
        idade = agora - modificado
        if chave not in vinculadas and idade > limite:
            resultado.append((chave, modificado, idade.total_seconds() / 3600))
    return sorted(resultado)


def formatar_relatorio(orfaos: list[tuple[str, datetime, float]], prefixo: str, idade_minima_horas: float) -> str:
    linhas = [
        f"Relatório de órfãos (DRY-RUN — nada é apagado) prefixo={prefixo!r} idade>{idade_minima_horas}h",
        f"{'CHAVE':<60} {'LAST_MODIFIED (UTC)':<20} IDADE_H",
    ]
    for chave, modificado, horas in orfaos:
        linhas.append(f"{chave:<60} {modificado.strftime('%Y-%m-%d %H:%M:%S'):<20} {horas:.1f}")
    linhas.append(f"Total de órfãos: {len(orfaos)}")
    return "\n".join(linhas)


def gerar_relatorio(
    storage,
    consulta_vinculos: Callable[[], Iterable[str]],
    prefixo: str = PREFIXO_PADRAO,
    idade_minima_horas: float = IDADE_MINIMA_HORAS_PADRAO,
    agora: datetime | None = None,
) -> tuple[str, list[tuple[str, datetime, float]]]:
    """Núcleo testável sem banco/MinIO: `consulta_vinculos` é injetada."""
    vinculadas = set(consulta_vinculos())
    sem_vinculo = set(storage.listar_orfaos(vinculadas, prefix=prefixo))
    objetos = [(k, m) for k, m in storage.list_objects(prefixo) if k in sem_vinculo]
    orfaos = calcular_orfaos(objetos, vinculadas, idade_minima_horas, agora)
    return formatar_relatorio(orfaos, prefixo, idade_minima_horas), orfaos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Relatório de órfãos do storage (somente dry-run, DEC-44).")
    parser.add_argument("--idade-minima-horas", type=float, default=IDADE_MINIMA_HORAS_PADRAO)
    parser.add_argument("--prefixo", default=PREFIXO_PADRAO)
    args = parser.parse_args(argv)

    from app.services.storage.s3_client import S3StorageClient

    relatorio, _ = gerar_relatorio(
        S3StorageClient(),
        lambda: asyncio.run(consultar_chaves_vinculadas()),
        args.prefixo,
        args.idade_minima_horas,
    )
    print(relatorio)
    return 0


if __name__ == "__main__":
    sys.exit(main())
