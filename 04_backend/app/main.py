"""Ponto de entrada da API FastAPI — scaffold inicial (BL-02).

Endpoints de domínio (edificações, contratos, autenticação, etc.) são
adicionados em tarefas subsequentes do backlog (BL-06 e seguintes). Ver
`00_docs/arquitetura.md` Seção 7 e `00_docs/projeto/decisoes.md` DEC-05.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.dados_mestre import router as dados_mestre_router
from app.core.config import get_settings
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dados_mestre_router)


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
    except Exception:  # noqa: BLE001 - qualquer falha de conectividade deve virar "unavailable"
        logger.exception("Healthcheck: falha ao conectar ao PostgreSQL")
        database_status = "unavailable"

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": database_status,
    }
