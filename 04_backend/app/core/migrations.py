"""Aplicação das migrations Alembic no boot da aplicação.

O serviço de produção (Render, runtime nativo Python) não expõe Pre-Deploy
Command, então `alembic upgrade head` nunca era executado e o schema do banco
não chegava a existir. Habilitado por `RUN_MIGRATIONS_ON_STARTUP=true`
(desligado por padrão, para não interferir em dev/testes/CI, onde o `alembic`
é chamado explicitamente).
"""
from pathlib import Path

from alembic.config import Config

from alembic import command
from app.core.config import get_settings

BACKEND_DIR = Path(__file__).resolve().parents[2]


def aplicar_migrations() -> None:
    """Executa `alembic upgrade head`. Bloqueante — chamar via `asyncio.to_thread`."""
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url)
    command.upgrade(config, "head")
