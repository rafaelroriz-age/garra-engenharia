"""Testes de integração do CRUD de Contratos (BL-09, RF-02, RF-12, RN-06, RN-09).

Cobre criação em cascata (Contrato + N executoras + N NBRs + Inspecao 1:1),
listagem com filtros, detalhe completo, atualização com substituição de
executoras/NBRs e as validações de RN-09 (ART de Fiscalização obrigatória).
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
from app.models import Contrato, ContratoExecutor, ContratoNbr, Edificacao, Inspecao, Responsavel, Usuario

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
    email = f"contratos-{uuid.uuid4()}@garra-engenharia.com.br"
    async with _TestSessionLocal() as session:
        usuario = Usuario(nome="Teste BL-09", email=email, senha_hash=hash_password("senha-forte"), ativo=True)
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
async def edificacao(db_session):
    obj = Edificacao(nome=f"Ed. BL-09 {uuid.uuid4()}", endereco="Rua dos Contratos, 1")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    yield obj
    await db_session.delete(obj)
    await db_session.commit()


@pytest_asyncio.fixture
async def fiscal(db_session):
    obj = Responsavel(nome="Eng. Fiscal BL-09", tipo="fiscal", crea="111111-GO")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    yield obj
    await db_session.delete(obj)
    await db_session.commit()


@pytest_asyncio.fixture
async def executora(db_session):
    obj = Responsavel(nome="Responsável Legal Executora BL-09", tipo="responsavel_legal")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    yield obj
    await db_session.delete(obj)
    await db_session.commit()


def _payload_contrato(edificacao_id, fiscal_id, executora_id):
    return {
        "edificacao_id": str(edificacao_id),
        "fiscal_id": str(fiscal_id),
        "numero": f"CT-{uuid.uuid4()}",
        "tipo_servico": "Fiscalização de obra",
        "art_fiscalizacao": "ART-FISC-001",
        "executores": [
            {
                "responsavel_legal_id": str(executora_id),
                "razao_social": "Executora Teste Ltda",
                "cnpj": "12.345.678/0001-90",
                "art_execucao": "ART-EXEC-001",
            }
        ],
        "nbrs": [{"codigo_nbr": "NBR 16747", "descricao": "Inspeção Predial"}],
    }


def _cleanup_contrato(contrato_id: uuid.UUID) -> None:
    """Versão síncrona (usa `asyncio.run`) — só pode ser chamada de fora de um event loop já rodando
    (ex.: corpo de uma test function síncrona), nunca de dentro de uma fixture async."""
    run_async(_cleanup_contrato_async(contrato_id))


async def _cleanup_contrato_async(contrato_id: uuid.UUID) -> None:
    async with _TestSessionLocal() as session:
        await session.execute(delete(Inspecao).where(Inspecao.contrato_id == contrato_id))
        await session.execute(delete(ContratoExecutor).where(ContratoExecutor.contrato_id == contrato_id))
        await session.execute(delete(ContratoNbr).where(ContratoNbr.contrato_id == contrato_id))
        await session.execute(delete(Contrato).where(Contrato.id == contrato_id))
        await session.commit()


@pytest_asyncio.fixture
async def contrato_criado(auth_headers, edificacao, fiscal, executora):
    response = client.post(
        "/api/v1/contratos",
        json=_payload_contrato(edificacao.id, fiscal.id, executora.id),
        headers=auth_headers,
    )
    body = response.json()
    yield body
    await _cleanup_contrato_async(uuid.UUID(body["id"]))


def test_criar_contrato_com_executora_e_nbr_cria_inspecao_em_cascata(
    auth_headers, edificacao, fiscal, executora
):
    response = client.post(
        "/api/v1/contratos",
        json=_payload_contrato(edificacao.id, fiscal.id, executora.id),
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["executores"]) == 1
    assert body["executores"][0]["art_execucao"] == "ART-EXEC-001"
    assert len(body["nbrs"]) == 1
    assert body["inspecao"] is not None
    assert body["inspecao"]["status"] == "em_andamento"

    _cleanup_contrato(uuid.UUID(body["id"]))


def test_criar_contrato_sem_art_fiscalizacao_retorna_422(auth_headers, edificacao, fiscal, executora):
    payload = _payload_contrato(edificacao.id, fiscal.id, executora.id)
    payload["art_fiscalizacao"] = "   "

    response = client.post("/api/v1/contratos", json=payload, headers=auth_headers)

    assert response.status_code == 422


def test_criar_contrato_com_edificacao_inexistente_retorna_404(auth_headers, fiscal, executora):
    payload = _payload_contrato(uuid.uuid4(), fiscal.id, executora.id)

    response = client.post("/api/v1/contratos", json=payload, headers=auth_headers)

    assert response.status_code == 404


def test_listar_contratos_filtrado_por_edificacao(auth_headers, contrato_criado, edificacao):
    response = client.get(
        "/api/v1/contratos", params={"edificacao_id": str(edificacao.id)}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert any(item["id"] == contrato_criado["id"] for item in body["items"])


def test_obter_contrato_detalhe_completo(auth_headers, contrato_criado):
    response = client.get(f"/api/v1/contratos/{contrato_criado['id']}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["executores"]) == 1
    assert len(body["nbrs"]) == 1


def test_atualizar_contrato_substitui_executoras(auth_headers, contrato_criado, edificacao, fiscal, executora):
    payload = _payload_contrato(edificacao.id, fiscal.id, executora.id)
    payload["numero"] = contrato_criado["numero"]
    payload["executores"][0]["razao_social"] = "Nova Executora Ltda"

    response = client.put(
        f"/api/v1/contratos/{contrato_criado['id']}", json=payload, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["executores"]) == 1
    assert body["executores"][0]["razao_social"] == "Nova Executora Ltda"
