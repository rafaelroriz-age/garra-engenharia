"""Cria (idempotente) um usuário auditor administrativo — BL-23.

Desde o hardening de segurança (OWASP A01), `POST /api/v1/auth/register` exige
um auditor autenticado, exceto quando o banco ainda não tem nenhum usuário.
Este script resolve o bootstrap de forma explícita e reproduzível, tanto na
primeira instalação quanto no ambiente de testes E2E/CI.

Uso (a partir de `04_backend/`):
    python -m app.scripts.seed_admin
    ADMIN_EMAIL=... ADMIN_SENHA=... python -m app.scripts.seed_admin

Nunca commitar credenciais reais: em produção, passar por variável de ambiente
e trocar a senha no primeiro acesso.
"""
import asyncio
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import SENHA_ADMIN_PADRAO_DEV, get_settings
from app.core.security import hash_password
from app.models import Usuario

SENHA_MINIMA = 8


async def criar_admin(email: str, senha: str, nome: str) -> str:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            existente = await session.scalar(select(Usuario).where(Usuario.email == email))
            if existente is not None:
                return f"Usuário '{email}' já existe (id={existente.id}) — nada a fazer."

            session.add(
                Usuario(
                    nome=nome,
                    email=email,
                    senha_hash=hash_password(senha),
                    ativo=True,
                    role="auditor",
                )
            )
            await session.commit()
            return f"Usuário auditor '{email}' criado."
    finally:
        await engine.dispose()


def main() -> int:
    email = os.getenv("ADMIN_EMAIL", "admin@garra-engenharia.com.br")
    senha = os.getenv("ADMIN_SENHA", "")
    nome = os.getenv("ADMIN_NOME", "Administrador")

    if not senha:
        # Senha previsível só em dev/teste (CI e E2E); fora disso exige ADMIN_SENHA (T110).
        if not get_settings().is_development:
            print("ERRO: defina ADMIN_SENHA fora de desenvolvimento.", file=sys.stderr)
            return 1
        senha = SENHA_ADMIN_PADRAO_DEV

    if len(senha) < SENHA_MINIMA:
        print(f"ERRO: ADMIN_SENHA precisa ter ao menos {SENHA_MINIMA} caracteres.", file=sys.stderr)
        return 1

    print(asyncio.run(criar_admin(email, senha, nome)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
