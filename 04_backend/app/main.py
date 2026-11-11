"""Ponto de entrada da API FastAPI — scaffold inicial (BL-02).

Endpoints de domínio (edificações, contratos, autenticação, etc.) são
adicionados em tarefas subsequentes do backlog (BL-06 e seguintes). Ver
`00_docs/arquitetura.md` Seção 7 e `00_docs/projeto/decisoes.md` DEC-05.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.auth import router as auth_router
from app.api.v1.contratos import router as contratos_router
from app.api.v1.dados_mestre import router as dados_mestre_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.edificacoes import router as edificacoes_router
from app.api.v1.fotos import router as fotos_router
from app.api.v1.inspecoes import router as inspecoes_router
from app.api.v1.ocorrencias import router as ocorrencias_router
from app.api.v1.portal import router as portal_router
from app.api.v1.relatorios import router as relatorios_router
from app.api.v1.responsaveis import router as responsaveis_router
from app.api.v1.visitas import router as visitas_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.core.migrations import aplicar_migrations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Garante o schema do banco antes de servir tráfego, quando habilitado."""
    if settings.run_migrations_on_startup:
        logger.info("Aplicando migrations Alembic (RUN_MIGRATIONS_ON_STARTUP=true)...")
        await asyncio.to_thread(aplicar_migrations)
        logger.info("Migrations aplicadas com sucesso.")
    yield

# Documentação interativa só em desenvolvimento (OWASP A05, arquitetura.md Seção 10.1).
_docs_habilitados = settings.is_development

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if _docs_habilitados else None,
    redoc_url="/redoc" if _docs_habilitados else None,
    openapi_url="/openapi.json" if _docs_habilitados else None,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware, hsts=not settings.is_development)
app.add_middleware(RequestIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(dados_mestre_router)
app.include_router(auth_router)
app.include_router(edificacoes_router)
app.include_router(contratos_router)
app.include_router(responsaveis_router)
app.include_router(inspecoes_router)
app.include_router(visitas_router)
app.include_router(fotos_router)
app.include_router(ocorrencias_router)
app.include_router(dashboard_router)
app.include_router(portal_router)
app.include_router(relatorios_router)


@app.get("/health", tags=["health"], summary="Healthcheck da API e do PostgreSQL")
async def health() -> dict:
    """Retorna o status da API e a conectividade com o PostgreSQL.

    Sempre responde HTTP 200: o campo `database` indica `ok` ou `unavailable`
    para permitir diagnóstico sem derrubar sondas de liveness simples.
    """
    database_status = "ok"
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Healthcheck: falha ao conectar ao PostgreSQL")
        database_status = "unavailable"

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": database_status,
    }
