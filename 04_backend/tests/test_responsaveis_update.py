"""Testes de integração de `PUT /api/v1/responsaveis/{id}` (DEC-50).

Mesmo padrão de `tests/test_responsaveis.py`: PostgreSQL real, override de
`get_db`, autenticação por JWT e erros RFC 7807 (DEC-11). Só o `auditor`
atualiza (RN-18, DEC-27); `auxiliar` e `cliente` recebem 403.
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
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Responsavel, Usuario

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)


async def _criar_usuario_async(role: str) -> uuid.UUID:
    async with _TestSessionLocal() as session:
        usuario = Usuario(
            nome=f"Usuário {role} DEC-50",
            email=f"{role}-dec50-{uuid.uuid4()}@garra-engenharia.com.br",
            senha_hash=hash_password("senha-forte-123"),
            ativo=True,
            role=role,
        )
        session.add(usuario)
        await session.commit()
        await session.refresh(usuario)
        return usuario.id


async def _criar_responsavel_async(**campos) -> uuid.UUID:
    async with _TestSessionLocal() as session:
        responsavel = Responsavel(**campos)
        session.add(responsavel)
        await session.commit()
        await session.refresh(responsavel)
        return responsavel.id


async def _limpar_async(responsavel_ids: list[uuid.UUID], usuario_ids: list[uuid.UUID]) -> None:
    async with _TestSessionLocal() as session:
        await session.execute(delete(Responsavel).where(Responsavel.id.in_(responsavel_ids)))
        await session.execute(delete(Usuario).where(Usuario.id.in_(usuario_ids)))
        await session.commit()


def _token(usuario_id: uuid.UUID) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario_id))}"}


def _ler_responsavel(responsavel_id: uuid.UUID) -> dict:
    return client.get(f"/api/v1/responsaveis/{responsavel_id}", headers=_auditor_headers).json()


@pytest_asyncio.fixture
async def usuarios():
    ids = {role: await _criar_usuario_async(role) for role in ("auditor", "auxiliar", "cliente")}
    yield ids
    await _limpar_async([], list(ids.values()))


@pytest_asyncio.fixture
async def responsavel():
    rid = await _criar_responsavel_async(
        nome="Fiscal Original DEC-50",
        tipo="fiscal",
        crea="111111-GO",
        email="original@garra-engenharia.com.br",
        telefone="62 99999-0000",
    )
    yield rid
    await _limpar_async([rid], [])


_auditor_headers: dict = {}


def _set_auditor(usuarios: dict) -> None:
    global _auditor_headers
    _auditor_headers = _token(usuarios["auditor"])


def test_auditor_atualiza_e_persiste(usuarios, responsavel):
    _set_auditor(usuarios)
    response = client.put(
        f"/api/v1/responsaveis/{responsavel}",
        json={"nome": "Fiscal Novo DEC-50", "tipo": "rte", "crea": "222222-GO"},
        headers=_auditor_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == "Fiscal Novo DEC-50"
    assert body["tipo"] == "rte"
    assert body["crea"] == "222222-GO"

    lido = _ler_responsavel(responsavel)
    assert lido["nome"] == "Fiscal Novo DEC-50"
    assert lido["crea"] == "222222-GO"


def test_atualizacao_parcial_preserva_campos_omitidos(usuarios, responsavel):
    _set_auditor(usuarios)
    response = client.put(
        f"/api/v1/responsaveis/{responsavel}",
        json={"telefone": "62 98888-1111"},
        headers=_auditor_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["telefone"] == "62 98888-1111"
    assert body["nome"] == "Fiscal Original DEC-50"
    assert body["tipo"] == "fiscal"
    assert body["crea"] == "111111-GO"
    assert body["email"] == "original@garra-engenharia.com.br"


def test_corpo_vazio_nao_altera_nada(usuarios, responsavel):
    _set_auditor(usuarios)
    antes = _ler_responsavel(responsavel)
    response = client.put(f"/api/v1/responsaveis/{responsavel}", json={}, headers=_auditor_headers)

    assert response.status_code == 200
    assert response.json() == antes


def test_null_explicito_em_campo_nao_nulo_retorna_422(usuarios, responsavel):
    _set_auditor(usuarios)
    response = client.put(
        f"/api/v1/responsaveis/{responsavel}",
        json={"nome": None},
        headers=_auditor_headers,
    )

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert _ler_responsavel(responsavel)["nome"] == "Fiscal Original DEC-50"


def test_payload_invalido_retorna_422(usuarios, responsavel):
    _set_auditor(usuarios)
    response = client.put(
        f"/api/v1/responsaveis/{responsavel}",
        json={"qualificacoes": "nao-e-lista"},
        headers=_auditor_headers,
    )

    assert response.status_code == 422


def test_id_inexistente_retorna_404_rfc7807(usuarios):
    _set_auditor(usuarios)
    response = client.put(
        f"/api/v1/responsaveis/{uuid.uuid4()}",
        json={"nome": "Fantasma"},
        headers=_auditor_headers,
    )

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"


def test_auxiliar_recebe_403_e_nada_muda(usuarios, responsavel):
    response = client.put(
        f"/api/v1/responsaveis/{responsavel}",
        json={"nome": "Invasor"},
        headers=_token(usuarios["auxiliar"]),
    )

    assert response.status_code == 403
    _set_auditor(usuarios)
    assert _ler_responsavel(responsavel)["nome"] == "Fiscal Original DEC-50"


def test_cliente_recebe_403(usuarios, responsavel):
    response = client.put(
        f"/api/v1/responsaveis/{responsavel}",
        json={"nome": "Invasor"},
        headers=_token(usuarios["cliente"]),
    )

    assert response.status_code == 403


def test_sem_token_retorna_401(responsavel):
    response = client.put(f"/api/v1/responsaveis/{responsavel}", json={"nome": "Anônimo"})

    assert response.status_code == 401


def test_auditor_vincula_usuario_e_conflito_se_ja_vinculado(usuarios, responsavel):
    """`usuario_id` segue a regra do POST: só auditor; um usuário só pode ter um Responsável (409)."""
    _set_auditor(usuarios)
    cliente_id = usuarios["cliente"]
    outro_rid = run_async(_criar_responsavel_async(nome="Outro DEC-50", tipo="sindico"))
    try:
        ok = client.put(
            f"/api/v1/responsaveis/{responsavel}",
            json={"usuario_id": str(cliente_id)},
            headers=_auditor_headers,
        )
        assert ok.status_code == 200
        assert ok.json()["usuario_id"] == str(cliente_id)

        conflito = client.put(
            f"/api/v1/responsaveis/{outro_rid}",
            json={"usuario_id": str(cliente_id)},
            headers=_auditor_headers,
        )
        assert conflito.status_code == 409
        assert conflito.headers["content-type"] == "application/problem+json"
    finally:
        run_async(_limpar_async([outro_rid], []))


def test_usuario_inexistente_em_usuario_id_retorna_422(usuarios, responsavel):
    _set_auditor(usuarios)
    response = client.put(
        f"/api/v1/responsaveis/{responsavel}",
        json={"usuario_id": str(uuid.uuid4())},
        headers=_auditor_headers,
    )

    assert response.status_code == 422
    assert _ler_responsavel(responsavel)["usuario_id"] is None
