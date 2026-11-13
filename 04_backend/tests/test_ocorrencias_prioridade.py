"""Testes de integração da prioridade sugerida/sobrescrita (BL-15, RN-04, DEC-29)."""
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
    Ocorrencia,
    Responsavel,
    SistemaPredial,
    Subsistema,
    Usuario,
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
async def auth():
    email = f"prioridade-{uuid.uuid4()}@garra-engenharia.com.br"
    async with _TestSessionLocal() as session:
        usuario = Usuario(nome="Teste BL-15", email=email, senha_hash=hash_password("senha-forte"), ativo=True)
        session.add(usuario)
        await session.commit()
        await session.refresh(usuario)
        usuario_id = usuario.id

    token = create_access_token(subject=str(usuario_id))
    yield {"Authorization": f"Bearer {token}", "usuario_id": usuario_id}

    async with _TestSessionLocal() as session:
        await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
        await session.commit()


@pytest_asyncio.fixture
async def inspecao_context(db_session):
    edificacao = Edificacao(nome=f"Ed. BL-15 {uuid.uuid4()}", endereco="Rua da Prioridade, 15")
    fiscal = Responsavel(nome="Eng. Fiscal BL-15", tipo="fiscal", crea="151515-GO")
    db_session.add_all([edificacao, fiscal])
    await db_session.commit()
    await db_session.refresh(edificacao)
    await db_session.refresh(fiscal)

    contrato = Contrato(
        edificacao_id=edificacao.id,
        fiscal_id=fiscal.id,
        numero=f"CT-BL15-{uuid.uuid4()}",
        tipo_servico="RFO",
        status="EM_ANDAMENTO",
        art_fiscalizacao="ART-015",
    )
    db_session.add(contrato)
    await db_session.commit()
    await db_session.refresh(contrato)

    inspecao = Inspecao(contrato_id=contrato.id, tipo="RFO", status="EM_ANDAMENTO")
    db_session.add(inspecao)
    await db_session.commit()
    await db_session.refresh(inspecao)

    sistema = SistemaPredial(nome=f"Sistema BL-15 {uuid.uuid4()}", ordem=10)
    db_session.add(sistema)
    await db_session.flush()

    subsistema = Subsistema(sistema_id=sistema.id, nome="Subsistema BL-15", ordem=1)
    db_session.add(subsistema)
    await db_session.commit()
    await db_session.refresh(sistema)
    await db_session.refresh(subsistema)

    yield {"inspecao": inspecao, "sistema": sistema, "subsistema": subsistema}

    await db_session.execute(delete(Ocorrencia).where(Ocorrencia.inspecao_id == inspecao.id))
    await db_session.delete(inspecao)
    await db_session.delete(contrato)
    await db_session.delete(fiscal)
    await db_session.delete(subsistema)
    await db_session.delete(sistema)
    await db_session.delete(edificacao)
    await db_session.commit()


def _base_payload(inspecao_context, **sobrescritas):
    payload = {
        "inspecao_id": str(inspecao_context["inspecao"].id),
        "sistema_id": str(inspecao_context["sistema"].id),
        "subsistema_id": str(inspecao_context["subsistema"].id),
        "situacao": "NAO_CONFORME",
        "classificacao": "ANOMALIA",
        "tipo_anomalia": "Fissura",
        "grau_risco": "CRITICO",
    }
    payload.update(sobrescritas)
    return payload


def test_criar_sem_prioridade_deriva_sugestao_do_grau_risco(auth, inspecao_context):
    response = client.post(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        json=_base_payload(inspecao_context, grau_risco="CRITICO"),
        headers=auth["Authorization"],
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["prioridade"] == 5
    assert corpo["prioridade_sugerida"] == 5
    assert corpo["prioridade_ajustada_por_id"] is None
    assert corpo["prioridade_ajustada_em"] is None


def test_criar_prioridade_igual_a_sugestao_nao_registra_ajuste(auth, inspecao_context):
    response = client.post(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        json=_base_payload(inspecao_context, grau_risco="MEDIO", prioridade=3),
        headers=auth["Authorization"],
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["prioridade"] == 3
    assert corpo["prioridade_sugerida"] == 3
    assert corpo["prioridade_ajustada_por_id"] is None


def test_criar_sobrescrita_registra_autoria_do_ajuste(auth, inspecao_context):
    response = client.post(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        json=_base_payload(inspecao_context, grau_risco="MEDIO", prioridade=5),
        headers=auth["Authorization"],
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["prioridade"] == 5
    assert corpo["prioridade_sugerida"] == 3
    assert corpo["prioridade_ajustada_por_id"] == str(auth["usuario_id"])
    assert corpo["prioridade_ajustada_em"] is not None


def test_criar_conforme_prioridade_nao_aplicavel(auth, inspecao_context):
    response = client.post(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        json=_base_payload(
            inspecao_context,
            situacao="CONFORME",
            classificacao="NAO_SE_APLICA",
            tipo_anomalia=None,
            grau_risco="MINIMO",
        ),
        headers=auth["Authorization"],
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["prioridade"] == 0
    assert corpo["prioridade_sugerida"] == 0
    assert corpo["prioridade_ajustada_por_id"] is None


def test_atualizar_sobrescrita_registra_autoria_do_ajuste(auth, inspecao_context):
    criado = client.post(
        f"/api/v1/inspecoes/{inspecao_context['inspecao'].id}/ocorrencias",
        json=_base_payload(inspecao_context, grau_risco="MEDIO"),
        headers=auth["Authorization"],
    ).json()
    assert criado["prioridade"] == 3
    assert criado["prioridade_ajustada_por_id"] is None

    atualizado = client.put(
        f"/api/v1/ocorrencias/{criado['id']}",
        json=_base_payload(inspecao_context, grau_risco="CRITICO", prioridade=3),
        headers=auth["Authorization"],
    )

    assert atualizado.status_code == 200
    corpo = atualizado.json()
    assert corpo["prioridade"] == 3
    assert corpo["prioridade_sugerida"] == 5
    assert corpo["prioridade_ajustada_por_id"] == str(auth["usuario_id"])
    assert corpo["prioridade_ajustada_em"] is not None
