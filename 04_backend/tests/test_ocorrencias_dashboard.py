"""Testes de integração para ocorrências e dashboard (BL-14, BL-16)."""
import uuid
from datetime import date

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Contrato, Edificacao, Inspecao, Ocorrencia, Responsavel, Subsistema, SistemaPredial, Usuario

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
    email = f"ocorrencias-{uuid.uuid4()}@garra-engenharia.com.br"
    async with _TestSessionLocal() as session:
        usuario = Usuario(nome="Teste BL-14", email=email, senha_hash=hash_password("senha-forte"), ativo=True)
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
async def inspecao_context(db_session):
    edificacao = Edificacao(nome=f"Ed. BL-14 {uuid.uuid4()}", endereco="Rua das Ocorrências, 100")
    fiscal = Responsavel(nome="Eng. Fiscal BL-14", tipo="fiscal", crea="333333-GO")
    db_session.add_all([edificacao, fiscal])
    await db_session.commit()
    await db_session.refresh(edificacao)
    await db_session.refresh(fiscal)

    contrato = Contrato(
        edificacao_id=edificacao.id,
        fiscal_id=fiscal.id,
        numero=f"CT-BL14-{uuid.uuid4()}",
        tipo_servico="RFO",
        status="EM_ANDAMENTO",
        art_fiscalizacao="ART-001",
    )
    db_session.add(contrato)
    await db_session.commit()
    await db_session.refresh(contrato)

    inspecao = Inspecao(contrato_id=contrato.id, tipo="RFO", status="EM_ANDAMENTO")
    db_session.add(inspecao)
    await db_session.commit()
    await db_session.refresh(inspecao)

    sistema = SistemaPredial(nome=f"Sistema BL-14 {uuid.uuid4()}", ordem=10)
    db_session.add(sistema)
    await db_session.flush()

    subsistema = Subsistema(sistema_id=sistema.id, nome="Subsistema BL-14", ordem=1)
    db_session.add(subsistema)
    await db_session.commit()
    await db_session.refresh(sistema)
    await db_session.refresh(subsistema)

    yield {"edificacao": edificacao, "inspecao": inspecao, "sistema": sistema, "subsistema": subsistema}

    await db_session.execute(delete(Ocorrencia).where(Ocorrencia.inspecao_id == inspecao.id))
    await db_session.delete(inspecao)
    await db_session.delete(contrato)
    await db_session.delete(fiscal)
    await db_session.delete(subsistema)
    await db_session.delete(sistema)
    await db_session.delete(edificacao)
    await db_session.commit()


def test_criar_e_listar_ocorrencias(auth_headers, inspecao_context):
    payload = {
        "inspecao_id": str(inspecao_context["inspecao"].id),
        "sistema_id": str(inspecao_context["sistema"].id),
        "subsistema_id": str(inspecao_context["subsistema"].id),
        "localizacao": "Andar 1",
        "situacao": "NAO_CONFORME",
        "classificacao": "ANOMALIA",
        "tipo_anomalia": "Fissura",
        "grau_risco": "MEDIO",
        "prioridade": 3,
        "descricao": "Anomalia detectada no subsistema",
    }

    response = client.post(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["sistema_id"] == str(inspecao_context["sistema"].id)
    assert body["seq_numero"] == 1

    list_response = client.get(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) >= 1


def test_criar_ocorrencia_rejeita_prioridade_fora_do_intervalo(auth_headers, inspecao_context):
    payload = {
        "inspecao_id": str(inspecao_context["inspecao"].id),
        "sistema_id": str(inspecao_context["sistema"].id),
        "subsistema_id": str(inspecao_context["subsistema"].id),
        "situacao": "NAO_CONFORME",
        "classificacao": "ANOMALIA",
        "tipo_anomalia": "Fissura",
        "grau_risco": "MEDIO",
        "prioridade": 7,
    }

    response = client.post(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.json()["type"].endswith("/ocorrencia-prioridade-invalida")


def test_dashboard_edificacao_retorna_agregados(auth_headers, inspecao_context):
    payload_1 = {
        "inspecao_id": str(inspecao_context["inspecao"].id),
        "sistema_id": str(inspecao_context["sistema"].id),
        "subsistema_id": str(inspecao_context["subsistema"].id),
        "situacao": "NAO_CONFORME",
        "classificacao": "FALHA",
        "tipo_falha": "Vazamento",
        "grau_risco": "CRITICO",
        "prioridade": 5,
    }
    payload_2 = {
        "inspecao_id": str(inspecao_context["inspecao"].id),
        "sistema_id": str(inspecao_context["sistema"].id),
        "subsistema_id": str(inspecao_context["subsistema"].id),
        "situacao": "CONFORME",
        "classificacao": "NAO_SE_APLICA",
        "grau_risco": "MINIMO",
        "prioridade": 1,
    }

    assert client.post(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        json=payload_1,
        headers=auth_headers,
    ).status_code == 201
    assert client.post(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        json=payload_2,
        headers=auth_headers,
    ).status_code == 201

    response = client.get(
        f"/api/v1/edificacoes/{inspecao_context['edificacao'].id}/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["edificacao_id"] == str(inspecao_context["edificacao"].id)
    assert any(item["sistema_id"] == str(inspecao_context["sistema"].id) for item in body["conformidade_por_sistema"])
    assert any(item["sistema_id"] == str(inspecao_context["sistema"].id) for item in body["grau_risco_por_sistema"])
