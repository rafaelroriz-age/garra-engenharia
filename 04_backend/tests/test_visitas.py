"""Testes de integração de Visitas e Inspeção (BL-10, RF-03, RN-01, RN-02).

Cobre criação de visita com `seq_numero` sequencial automático, atualização,
adição de mão de obra/medição e o detalhe da Inspeção com visitas ordenadas.
"""
import asyncio
import uuid

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import (
    Contrato,
    Edificacao,
    Inspecao,
    Responsavel,
    Usuario,
    Visita,
    VisitaMaoObra,
    VisitaMedicao,
)

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
    email = f"visitas-{uuid.uuid4()}@garra-engenharia.com.br"
    async with _TestSessionLocal() as session:
        usuario = Usuario(nome="Teste BL-10", email=email, senha_hash=hash_password("senha-forte"), ativo=True)
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
async def inspecao(db_session):
    edificacao = Edificacao(nome=f"Ed. BL-10 {uuid.uuid4()}", endereco="Rua das Visitas, 1")
    fiscal = Responsavel(nome="Eng. Fiscal BL-10", tipo="fiscal", crea="222222-GO")
    db_session.add_all([edificacao, fiscal])
    await db_session.commit()
    await db_session.refresh(edificacao)
    await db_session.refresh(fiscal)

    contrato = Contrato(
        edificacao_id=edificacao.id,
        fiscal_id=fiscal.id,
        numero=f"CT-BL10-{uuid.uuid4()}",
        tipo_servico="Fiscalização de obra",
        status="em_andamento",
        art_fiscalizacao="ART-001",
    )
    db_session.add(contrato)
    await db_session.commit()
    await db_session.refresh(contrato)

    obj = Inspecao(contrato_id=contrato.id, tipo="RFO", status="em_andamento")
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)

    yield obj

    await db_session.delete(obj)
    await db_session.delete(contrato)
    await db_session.delete(fiscal)
    await db_session.delete(edificacao)
    await db_session.commit()


def _cleanup_visita(visita_id: uuid.UUID) -> None:
    async def _delete() -> None:
        async with _TestSessionLocal() as session:
            await session.execute(delete(VisitaMaoObra).where(VisitaMaoObra.visita_id == visita_id))
            await session.execute(delete(VisitaMedicao).where(VisitaMedicao.visita_id == visita_id))
            await session.execute(delete(Visita).where(Visita.id == visita_id))
            await session.commit()

    # Loop próprio, sem registrá-lo como loop corrente: `asyncio.run` faz `set_event_loop(None)` ao
    # terminar e derruba o loop de sessão do pytest-asyncio para os testes async seguintes
    # ("There is no current event loop in thread 'MainThread'" em test_visitas_lacunas.py).
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_delete())
    finally:
        loop.close()


def test_criar_visita_atribui_seq_numero_sequencial(auth_headers, inspecao):
    resp1 = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-07-01", "servicos_executados": "Fundação"},
        headers=auth_headers,
    )
    resp2 = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-07-02", "servicos_executados": "Alvenaria"},
        headers=auth_headers,
    )

    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["seq_numero"] == 1
    assert resp2.json()["seq_numero"] == 2

    _cleanup_visita(uuid.UUID(resp1.json()["id"]))
    _cleanup_visita(uuid.UUID(resp2.json()["id"]))


def test_criar_visita_sem_servicos_executados_retorna_422(auth_headers, inspecao):
    response = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-07-01", "servicos_executados": "   "},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_criar_visita_em_inspecao_inexistente_retorna_404(auth_headers):
    response = client.post(
        f"/api/v1/inspecoes/{uuid.uuid4()}/visitas",
        json={"data": "2026-07-01", "servicos_executados": "Fundação"},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_obter_inspecao_com_visitas_ordenadas(auth_headers, inspecao):
    resp1 = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-07-01", "servicos_executados": "Fundação"},
        headers=auth_headers,
    )
    resp2 = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-07-02", "servicos_executados": "Alvenaria"},
        headers=auth_headers,
    )

    response = client.get(f"/api/v1/inspecoes/{inspecao.id}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    seq_numeros = [v["seq_numero"] for v in body["visitas"]]
    assert seq_numeros == sorted(seq_numeros)

    _cleanup_visita(uuid.UUID(resp1.json()["id"]))
    _cleanup_visita(uuid.UUID(resp2.json()["id"]))


def test_atualizar_visita(auth_headers, inspecao):
    criada = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-07-01", "servicos_executados": "Fundação"},
        headers=auth_headers,
    ).json()

    response = client.put(
        f"/api/v1/visitas/{criada['id']}",
        json={"data": "2026-07-01", "servicos_executados": "Fundação concluída", "observacoes": "Sem intercorrências"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["servicos_executados"] == "Fundação concluída"

    _cleanup_visita(uuid.UUID(criada["id"]))


def test_adicionar_mao_obra_e_medicao(auth_headers, inspecao):
    criada = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-07-01", "servicos_executados": "Fundação"},
        headers=auth_headers,
    ).json()

    resp_mao_obra = client.post(
        f"/api/v1/visitas/{criada['id']}/mao-obra",
        json={"funcao": "Pedreiro", "quantidade": 3},
        headers=auth_headers,
    )
    resp_medicao = client.post(
        f"/api/v1/visitas/{criada['id']}/medicoes",
        json={"descricao": "Concreto lançado", "quantidade": 12.5, "unidade": "m3"},
        headers=auth_headers,
    )

    assert resp_mao_obra.status_code == 201
    assert resp_mao_obra.json()["funcao"] == "Pedreiro"
    assert resp_medicao.status_code == 201
    assert resp_medicao.json()["unidade"] == "m3"

    _cleanup_visita(uuid.UUID(criada["id"]))
