"""Testes do gabarito de sistemas prediais/subsistemas/tipos de anomalia/falha/localizações (BL-05, RF-10).

Valida o parser de `RFO_INSPECAO.md` (sem banco de dados), o seed idempotente
contra o PostgreSQL real e os endpoints de dados mestre de
`00_docs/arquitetura.md` Seção 4.
"""
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.scripts.rfo_gabarito_parser import build_gabarito
from app.scripts.seed_gabarito import seed_gabarito

# Engine próprio com `NullPool` para os testes deste módulo (mesmo padrão de
# `tests/conftest.py`): o `TestClient` (sem uso como context manager) abre um
# novo loop de eventos a cada requisição, e o pool padrão de
# `app.core.database.engine` reaproveita conexões `asyncpg` entre requisições
# — causando "attached to a different loop" / "Event loop is closed" no
# Windows (ProactorEventLoop). `NullPool` evita qualquer reuso de conexão.
_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _gabarito_seeded() -> dict[str, int]:
    """Garante que o gabarito esteja populado (idempotente) antes dos testes de endpoint."""
    async with _TestSessionLocal() as session:
        return await seed_gabarito(session)


def test_parse_gabarito_extrai_15_sistemas_com_subsistemas():
    """O gabarito de `RFO_INSPECAO.md` tem 15 Sistemas Prediais, todos com ao menos 1 subsistema."""
    gabarito = build_gabarito()
    sistemas = gabarito["sistemas"]

    assert len(sistemas) == 15
    for sistema in sistemas:
        subsistemas = gabarito["subsistemas_por_sistema"].get(sistema, [])
        assert len(subsistemas) > 0, f"Sistema '{sistema}' sem subsistemas extraídos"


def test_parse_gabarito_tipos_anomalia_falha_e_localizacoes():
    gabarito = build_gabarito()

    assert gabarito["tipos_anomalia"] == [
        "Endógena",
        "Exógena",
        "Natural",
        "Funcional",
        "Endógena / Natural",
        "Endógena / Funcional",
    ]
    assert gabarito["tipos_falha"] == [
        "De Execução",
        "De Execução / Gerencial",
        "De Planejamento",
        "Planejamento / Execução",
        "Planejamento / Gerencial",
        "Gerencial",
        "Operacional",
        "Operacional / Gerencial",
        "Planejamento / Operacional",
    ]
    assert len(gabarito["localizacoes"]) == 47


def test_endpoint_sistemas_prediais_lista_15_com_subsistemas():
    response = client.get("/api/v1/sistemas-prediais")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 15
    for sistema in body:
        assert sistema["nome"]
        assert isinstance(sistema["subsistemas"], list)
        assert len(sistema["subsistemas"]) > 0


def test_endpoint_tipos_anomalia_lista_6():
    response = client.get("/api/v1/gabarito/tipos-anomalia")

    assert response.status_code == 200
    assert len(response.json()) == 6


def test_endpoint_tipos_falha_lista_9():
    response = client.get("/api/v1/gabarito/tipos-falha")

    assert response.status_code == 200
    assert len(response.json()) == 9


def test_endpoint_localizacoes_lista_47():
    response = client.get("/api/v1/gabarito/localizacoes")

    assert response.status_code == 200
    assert len(response.json()) == 47
