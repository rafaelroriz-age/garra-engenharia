"""Testes de integração do endpoint de Responsável (fora da Seção 4 original,
DEC-23 — criado ao implementar os testes E2E de BL-21 para desbloquear a
criação de Contratos via API/UI).

Mesmo padrão de `tests/test_edificacoes.py`: PostgreSQL real, override de
`get_db`, autenticação obrigatória e formato de erro RFC 7807 (DEC-11).
"""
import uuid
from asyncio import run as run_async

import pytest_asyncio
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Responsavel, Usuario
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)


async def _cleanup_responsavel_async(responsavel_id: uuid.UUID) -> None:
    async with _TestSessionLocal() as session:
        await session.execute(delete(Responsavel).where(Responsavel.id == responsavel_id))
        await session.commit()


def _cleanup_responsavel(responsavel_id: str) -> None:
    run_async(_cleanup_responsavel_async(uuid.UUID(responsavel_id)))


@pytest_asyncio.fixture
async def auth_headers():
    email = f"responsaveis-{uuid.uuid4()}@garra-engenharia.com.br"
    async with _TestSessionLocal() as session:
        usuario = Usuario(nome="Teste BL-21", email=email, senha_hash=hash_password("senha-forte"), ativo=True)
        session.add(usuario)
        await session.commit()
        await session.refresh(usuario)
        usuario_id = usuario.id

    token = create_access_token(subject=str(usuario_id))
    yield {"Authorization": f"Bearer {token}"}

    async with _TestSessionLocal() as session:
        await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
        await session.commit()


def test_criar_responsavel_retorna_201(auth_headers):
    nome = f"Eng. Fiscal Teste {uuid.uuid4()}"
    response = client.post(
        "/api/v1/responsaveis",
        json={"nome": nome, "tipo": "fiscal", "crea": "999999-GO"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nome"] == nome
    assert body["tipo"] == "fiscal"

    _cleanup_responsavel(body["id"])


def test_criar_responsavel_sem_auth_retorna_401():
    response = client.post("/api/v1/responsaveis", json={"nome": "X", "tipo": "fiscal"})
    assert response.status_code == 401


def test_listar_responsaveis_filtra_por_tipo(auth_headers):
    criado = client.post(
        "/api/v1/responsaveis",
        json={"nome": f"Contratante Teste {uuid.uuid4()}", "tipo": "sindico"},
        headers=auth_headers,
    ).json()

    response = client.get("/api/v1/responsaveis?tipo=sindico", headers=auth_headers)
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert criado["id"] in ids

    _cleanup_responsavel(criado["id"])


def test_obter_responsavel_inexistente_retorna_404_rfc7807(auth_headers):
    response = client.get(f"/api/v1/responsaveis/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
