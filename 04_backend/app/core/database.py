"""Engine e sessão assíncrona do SQLAlchemy 2 (DEC-07).

Os modelos ORM e as migrations Alembic são adicionados em BL-04
(`.github/prompts/17-modelagem-dados-migrations.prompt.md`). Este módulo apenas
estabelece a infraestrutura de conexão usada pelo healthcheck (BL-02).
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency do FastAPI que fornece uma sessão de banco de dados por requisição."""
    async with AsyncSessionLocal() as session:
        yield session
