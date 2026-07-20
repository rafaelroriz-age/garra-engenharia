"""Testes de autenticação JWT + bcrypt (BL-06, RNF-05, DEC-05).

Cobre: registro, login com sucesso, login com senha incorreta (401), acesso a
rota protegida sem token (401) e com token válido (200). Roda contra o
PostgreSQL real (mesmo padrão de `tests/test_gabarito.py`): usa engine próprio
com `NullPool` e sobrescreve `get_db` para evitar o problema de "event loop
diferente" do `TestClient` no Windows (ver `04_backend/README.md`/memória de
repo).
"""
import uuid
from asyncio import run as run_async

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models import Usuario

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)

EMAIL_EXISTENTE = "engenheiro.teste@garra-engenharia.com.br"
SENHA_EXISTENTE = "senha-super-secreta"


def _delete_usuario_por_email(email: str) -> None:
    """Remove um usuário criado por um teste síncrono (via `/register`), fora de fixtures async."""

    async def _delete() -> None:
        async with _TestSessionLocal() as session:
            await session.execute(delete(Usuario).where(Usuario.email == email))
            await session.commit()

    run_async(_delete())


@pytest_asyncio.fixture
async def usuario_existente():
    """Cria um usuário ativo diretamente no banco (fora dos endpoints) para os testes de login."""
    async with _TestSessionLocal() as session:
        usuario = Usuario(
            nome="Engenheiro de Teste",
            email=EMAIL_EXISTENTE,
            senha_hash=hash_password(SENHA_EXISTENTE),
            ativo=True,
        )
        session.add(usuario)
        await session.commit()
        await session.refresh(usuario)
        usuario_id = usuario.id

    yield usuario_id

    async with _TestSessionLocal() as session:
        await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
        await session.commit()


def test_register_cria_usuario_sem_expor_hash_da_senha():
    email = f"novo-{uuid.uuid4()}@garra-engenharia.com.br"
    response = client.post(
        "/api/v1/auth/register",
        json={"nome": "Novo Usuário", "email": email, "senha": "outra-senha-forte"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert body["ativo"] is True
    assert "senha" not in body
    assert "senha_hash" not in body

    _delete_usuario_por_email(email)


def test_register_com_email_duplicado_retorna_409(usuario_existente):
    response = client.post(
        "/api/v1/auth/register",
        json={"nome": "Duplicado", "email": EMAIL_EXISTENTE, "senha": "outra-senha-forte"},
    )

    assert response.status_code == 409


def test_login_com_sucesso_retorna_access_token(usuario_existente):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL_EXISTENTE, "senha": SENHA_EXISTENTE},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 0


def test_login_com_senha_incorreta_retorna_401(usuario_existente):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL_EXISTENTE, "senha": "senha-errada"},
    )

    assert response.status_code == 401


def test_acesso_a_rota_protegida_sem_token_retorna_401():
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_acesso_a_rota_protegida_com_token_valido_retorna_200(usuario_existente):
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL_EXISTENTE, "senha": SENHA_EXISTENTE},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == EMAIL_EXISTENTE
    assert "senha_hash" not in body


def test_acesso_a_rota_protegida_com_token_invalido_retorna_401():
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer token-invalido-e-mal-formado"},
    )

    assert response.status_code == 401
