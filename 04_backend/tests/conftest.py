"""Fixtures compartilhadas dos testes de integração (BL-04).

Usa `NullPool` para o engine assíncrono de testes: cada operação abre/fecha
uma conexão física própria, evitando problemas de reuso de conexão do
`asyncpg` observados no Windows com `ProactorEventLoop` quando o pool padrão
(`QueuePool`) é compartilhado entre fixtures/testes.
"""
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

test_engine = create_async_engine(settings.database_url, poolclass=NullPool, future=True)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session():
    """Sessão async de banco de dados isolada por teste (conexão própria via NullPool)."""
    async with TestSessionLocal() as session:
        yield session
