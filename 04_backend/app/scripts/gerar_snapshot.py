"""Gera `snapshot.enc`: a leitura da equipe cifrada com a senha da equipe (DEC-57, T81).

Uso (a partir de `04_backend/`):
    SNAPSHOT_SENHA=... python -m app.scripts.gerar_snapshot --saida <arquivo>
    SNAPSHOT_SENHA=... python -m app.scripts.gerar_snapshot --saida <arquivo> --somente-se-mudou

Variáveis de ambiente:
    SNAPSHOT_SENHA          senha da equipe (obrigatória, mínimo 16 caracteres; DEC-57).
    SNAPSHOT_USUARIO_EMAIL  e-mail do auditor de serviço usado na coleta
                            (padrão snapshot.servico@garra-engenharia.com.br; criado
                            com senha aleatória se não existir).

Com `--somente-se-mudou`, compara o SHA-256 das rotas (texto claro sem `gerado_em`)
com `<saida>.sha256`; se for igual, não grava nada e sai com código 3.

Códigos de saída: 0 gravado, 3 nada mudou, 2 configuração inválida, 1 erro.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.services.snapshot import (
    EMAIL_SERVICO_PADRAO,
    cifrar_snapshot,
    coletar_rotas,
    hash_rotas,
)
from app.services.snapshot.coletor import CONCORRENCIA_PADRAO

SENHA_MINIMA = 16
SAIDA_OK = 0
SAIDA_ERRO = 1
SAIDA_CONFIG = 2
SAIDA_SEM_MUDANCA = 3

logger = logging.getLogger("gerar_snapshot")


def _gravar_atomico(destino: Path, conteudo: str) -> None:
    temporario = destino.with_name(destino.name + ".tmp")
    temporario.write_text(conteudo, encoding="utf-8")
    os.replace(temporario, destino)


async def _gerar(saida: Path, senha: str, email: str, somente_se_mudou: bool) -> int:
    from app.main import app  # importa só aqui: o app lê settings no import

    engine = create_async_engine(get_settings().database_url, pool_size=CONCORRENCIA_PADRAO, future=True)
    try:
        resultado = await coletar_rotas(app, async_sessionmaker(bind=engine, expire_on_commit=False), email_servico=email)
    finally:
        await engine.dispose()

    arquivo_hash = saida.with_name(saida.name + ".sha256")
    digest = hash_rotas(resultado.rotas)
    if somente_se_mudou and saida.exists() and arquivo_hash.exists():
        if arquivo_hash.read_text(encoding="utf-8").strip() == digest:
            print(f"Snapshot sem mudanças ({len(resultado.rotas)} rotas, sha256 {digest[:12]}…).")
            return SAIDA_SEM_MUDANCA

    conteudo = {"gerado_em": datetime.now(UTC).isoformat(timespec="seconds"), "rotas": resultado.rotas}
    envelope = cifrar_snapshot(conteudo, senha)
    saida.parent.mkdir(parents=True, exist_ok=True)
    _gravar_atomico(saida, json.dumps(envelope, separators=(",", ":")))
    _gravar_atomico(arquivo_hash, digest + "\n")

    print(
        f"Snapshot gravado em {saida}: {len(resultado.rotas)} rotas, "
        f"{saida.stat().st_size} bytes, sha256 {digest[:12]}…"
    )
    if resultado.falhas:
        print(f"Rotas que falharam ({len(resultado.falhas)}), fora do snapshot:")
        for chave, status in sorted(resultado.falhas.items()):
            print(f"  HTTP {status}  {chave}")
    return SAIDA_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera o snapshot cifrado da leitura da equipe (DEC-57).")
    parser.add_argument("--saida", required=True, type=Path, help="Arquivo de saída (ex.: snapshot.enc).")
    parser.add_argument(
        "--somente-se-mudou",
        action="store_true",
        help="Não grava e sai com código 3 se o texto claro (sem gerado_em) não mudou.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)

    senha = os.environ.get("SNAPSHOT_SENHA", "")
    if len(senha) < SENHA_MINIMA:
        print(f"SNAPSHOT_SENHA ausente ou com menos de {SENHA_MINIMA} caracteres.", file=sys.stderr)
        return SAIDA_CONFIG
    email = os.environ.get("SNAPSHOT_USUARIO_EMAIL") or EMAIL_SERVICO_PADRAO

    try:
        return asyncio.run(_gerar(args.saida, senha, email, args.somente_se_mudou))
    except Exception as exc:  # o agente (T82) só precisa do código de saída e da mensagem
        print(f"Falha ao gerar o snapshot: {exc}", file=sys.stderr)
        return SAIDA_ERRO


if __name__ == "__main__":
    sys.exit(main())
