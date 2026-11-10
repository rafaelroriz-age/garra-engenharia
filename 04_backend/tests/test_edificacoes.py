"""Testes de integração do CRUD de Edificações (BL-08, RF-01).

Cobre os 4 endpoints de `00_docs/arquitetura.md` Seção 4 (listagem paginada
com filtro, criação, detalhe com contratos, atualização), autenticação
obrigatória (BL-06) e o formato de erro RFC 7807 (DEC-11). Roda contra o
PostgreSQL real (mesmo padrão de `tests/test_auth.py`/`test_gabarito.py`).
"""
import uuid

import pytest_asyncio
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Edificacao, Usuario
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


@pytest_asyncio.fixture
async def auth_headers():
    """Cria um usuário ativo e retorna os headers `Authorization: Bearer <token>`."""
    email = f"edificacoes-{uuid.uuid4()}@garra-engenharia.com.br"
    async with _TestSessionLocal() as session:
        usuario = Usuario(nome="Teste BL-08", email=email, senha_hash=hash_password("senha-forte"), ativo=True)
        session.add(usuario)
        await session.commit()
        await session.refresh(usuario)
        usuario_id = usuario.id

    token = create_access_token(subject=str(usuario_id))
    yield {"Authorization": f"Bearer {token}"}

    async with _TestSessionLocal() as session:
        await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
        await session.commit()


@pytest_asyncio.fixture
async def edificacao_criada(auth_headers):
    response = client.post(
        "/api/v1/edificacoes",
        json={"nome": f"Ed. Teste {uuid.uuid4()}", "endereco": "Rua das Flores, 100"},
        headers=auth_headers,
    )
    body = response.json()
    yield body

    async with _TestSessionLocal() as session:
        await session.execute(delete(Edificacao).where(Edificacao.id == uuid.UUID(body["id"])))
        await session.commit()


def test_criar_edificacao_retorna_201(auth_headers):
    nome = f"Cond. Teste {uuid.uuid4()}"
    response = client.post(
        "/api/v1/edificacoes",
        json={"nome": nome, "endereco": "Av. Central, 500", "tipologia": "Residencial"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nome"] == nome
    assert body["id"]

    _cleanup_edificacao(body["id"])


def _cleanup_edificacao(edificacao_id: str) -> None:
    """Helper síncrono para limpar edificações criadas fora de fixture (evita vazar dados de teste)."""
    from asyncio import run as run_async

    async def _delete() -> None:
        async with _TestSessionLocal() as session:
            await session.execute(delete(Edificacao).where(Edificacao.id == uuid.UUID(edificacao_id)))
            await session.commit()

    run_async(_delete())


def test_criar_edificacao_sem_autenticacao_retorna_401():
    response = client.post(
        "/api/v1/edificacoes", json={"nome": "Sem Auth", "endereco": "Rua X, 1"}
    )
    assert response.status_code == 401


def test_listar_edificacoes_paginado(auth_headers, edificacao_criada):
    response = client.get("/api/v1/edificacoes", params={"page": 1, "page_size": 20}, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert "items" in body and "total" in body
    assert any(item["id"] == edificacao_criada["id"] for item in body["items"])


def test_listar_edificacoes_filtro_por_nome(auth_headers, edificacao_criada):
    nome_busca = edificacao_criada["nome"][:10]
    response = client.get(
        "/api/v1/edificacoes", params={"nome": nome_busca}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert any(item["id"] == edificacao_criada["id"] for item in body["items"])


def test_obter_edificacao_com_historico_de_contratos(auth_headers, edificacao_criada):
    response = client.get(f"/api/v1/edificacoes/{edificacao_criada['id']}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == edificacao_criada["id"]
    assert body["contratos"] == []


def test_obter_edificacao_inexistente_retorna_404_rfc7807(auth_headers):
    response = client.get(f"/api/v1/edificacoes/{uuid.uuid4()}", headers=auth_headers)

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == 404
    assert body["type"].startswith("https://garra-engenharia/erros/")
    assert "title" in body and "detail" in body


def test_atualizar_edificacao(auth_headers, edificacao_criada):
    novo_nome = f"{edificacao_criada['nome']} - Atualizado"
    response = client.put(
        f"/api/v1/edificacoes/{edificacao_criada['id']}",
        json={"nome": novo_nome, "endereco": edificacao_criada["endereco"]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["nome"] == novo_nome
