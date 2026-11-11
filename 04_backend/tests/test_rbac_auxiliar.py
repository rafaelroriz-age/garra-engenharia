"""Testes de autorização por perfil — perfil `auxiliar` (BL-42, RN-18, DEC-27/ADR-14).

Cobre o que o auxiliar de campo PODE (visita, ocorrência, foto — com autoria
gravada em `criado_por_id`) e o que NÃO pode (edificação, contrato,
responsável, cadastro de usuário), além de confirmar que o perfil `cliente`
não alcança nenhuma rota interna.
"""
import uuid
from asyncio import run as run_async

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import (
    Contrato,
    Edificacao,
    Foto,
    Inspecao,
    Ocorrencia,
    Responsavel,
    SistemaPredial,
    Usuario,
    Visita,
)

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


async def _criar_usuario(role: str) -> uuid.UUID:
    async with _TestSessionLocal() as session:
        usuario = Usuario(
            nome=f"Usuário {role} BL-42",
            email=f"{role}-{uuid.uuid4()}@garra-engenharia.com.br",
            senha_hash=hash_password("senha-forte-123"),
            ativo=True,
            role=role,
        )
        session.add(usuario)
        await session.commit()
        await session.refresh(usuario)
        return usuario.id


async def _remover_usuario(usuario_id: uuid.UUID) -> None:
    async with _TestSessionLocal() as session:
        await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
        await session.commit()


def _headers(usuario_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario_id))}"}


@pytest_asyncio.fixture
async def auxiliar():
    usuario_id = await _criar_usuario("auxiliar")
    yield usuario_id
    await _remover_usuario(usuario_id)


@pytest_asyncio.fixture
async def auditor():
    usuario_id = await _criar_usuario("auditor")
    yield usuario_id
    await _remover_usuario(usuario_id)


@pytest_asyncio.fixture
async def cliente():
    usuario_id = await _criar_usuario("cliente")
    yield usuario_id
    await _remover_usuario(usuario_id)


@pytest_asyncio.fixture
async def inspecao(db_session):
    edificacao = Edificacao(nome=f"Ed. BL-42 {uuid.uuid4()}", endereco="Rua do Auxiliar, 42")
    fiscal = Responsavel(nome="Eng. Fiscal BL-42", tipo="fiscal", crea="424242-GO")
    db_session.add_all([edificacao, fiscal])
    await db_session.commit()
    await db_session.refresh(edificacao)
    await db_session.refresh(fiscal)

    contrato = Contrato(
        edificacao_id=edificacao.id,
        fiscal_id=fiscal.id,
        numero=f"CT-BL42-{uuid.uuid4()}",
        tipo_servico="Fiscalização de obra",
        status="em_andamento",
        art_fiscalizacao="ART-042",
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


def _png_minimo() -> bytes:
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format="PNG")
    return buffer.getvalue()


def _cleanup(model, registro_id: uuid.UUID) -> None:
    async def _delete() -> None:
        async with _TestSessionLocal() as session:
            await session.execute(delete(model).where(model.id == registro_id))
            await session.commit()

    run_async(_delete())


def _primeiro_sistema_predial() -> uuid.UUID | None:
    async def _buscar() -> uuid.UUID | None:
        async with _TestSessionLocal() as session:
            resultado = await session.execute(select(SistemaPredial.id).limit(1))
            return resultado.scalars().first()

    return run_async(_buscar())


# --- O que o auxiliar PODE fazer (dados de campo, RN-18) ---


def test_auxiliar_cria_visita_e_autoria_e_registrada(auxiliar, inspecao):
    response = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-09-10", "servicos_executados": "Concretagem da laje"},
        headers=_headers(auxiliar),
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["criado_por_id"] == str(auxiliar)
    _cleanup(Visita, uuid.UUID(corpo["id"]))


def test_auxiliar_cria_ocorrencia_e_autoria_e_registrada(auxiliar, inspecao):
    sistema_id = _primeiro_sistema_predial()
    if sistema_id is None:
        pytest.skip("Gabarito de sistemas prediais não semeado (rodar app.scripts.seed_gabarito).")

    response = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/ocorrencias",
        json={
            "inspecao_id": str(inspecao.id),
            "sistema_id": str(sistema_id),
            "situacao": "NAO_CONFORME",
            "classificacao": "ANOMALIA",
            "tipo_anomalia": "Fissura",
            "grau_risco": "MEDIO",
        },
        headers=_headers(auxiliar),
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["criado_por_id"] == str(auxiliar)
    _cleanup(Ocorrencia, uuid.UUID(corpo["id"]))


def test_auxiliar_vincula_foto_a_visita_com_autoria(auxiliar, inspecao):
    visita = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-09-10", "servicos_executados": "Registro fotográfico"},
        headers=_headers(auxiliar),
    ).json()

    # DEC-39: o vínculo exige chave emitida pelo servidor e existente no storage -> upload real antes.
    upload = client.post(
        "/api/v1/fotos/upload",
        files={"arquivo": ("f.png", _png_minimo(), "image/png")},
        headers=_headers(auxiliar),
    )
    assert upload.status_code == 201
    response = client.post(
        f"/api/v1/visitas/{visita['id']}/fotos",
        json={"storage_key": upload.json()["storage_key"], "origem": "upload_manual", "legenda": "Fachada"},
        headers=_headers(auxiliar),
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["criado_por_id"] == str(auxiliar)
    _cleanup(Foto, uuid.UUID(corpo["id"]))
    _cleanup(Visita, uuid.UUID(visita["id"]))


def test_auxiliar_le_edificacoes_e_dados_de_contrato(auxiliar):
    assert client.get("/api/v1/edificacoes", headers=_headers(auxiliar)).status_code == 200
    assert client.get("/api/v1/contratos", headers=_headers(auxiliar)).status_code == 200
    assert client.get("/api/v1/responsaveis", headers=_headers(auxiliar)).status_code == 200


# --- O que o auxiliar NÃO pode fazer (administração e responsabilidade técnica) ---


def test_auxiliar_nao_cria_edificacao(auxiliar):
    response = client.post(
        "/api/v1/edificacoes",
        json={"nome": "Edifício Proibido", "endereco": "Rua Bloqueada, 0"},
        headers=_headers(auxiliar),
    )

    assert response.status_code == 403
    assert response.json()["type"].endswith("/acesso-negado")


def test_auxiliar_nao_cria_responsavel(auxiliar):
    response = client.post(
        "/api/v1/responsaveis",
        json={"nome": "Responsável Proibido", "tipo": "fiscal"},
        headers=_headers(auxiliar),
    )

    assert response.status_code == 403


def test_auxiliar_nao_cria_contrato(auxiliar, inspecao):
    response = client.post(
        "/api/v1/contratos",
        json={
            "edificacao_id": str(uuid.uuid4()),
            "fiscal_id": str(uuid.uuid4()),
            "numero": "CT-PROIBIDO",
            "tipo_servico": "Fiscalização de obra",
            "status": "em_andamento",
            "art_fiscalizacao": "ART-000",
            "executores": [],
            "nbrs": [],
        },
        headers=_headers(auxiliar),
    )

    assert response.status_code == 403


def test_auxiliar_nao_cadastra_usuario(auxiliar):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Novo Auditor",
            "email": f"novo-{uuid.uuid4()}@garra-engenharia.com.br",
            "senha": "senha-forte-123",
        },
        headers=_headers(auxiliar),
    )

    assert response.status_code == 403


# --- O perfil cliente não alcança rotas internas (OWASP A01) ---


def test_cliente_nao_acessa_rotas_internas(cliente):
    assert client.get("/api/v1/edificacoes", headers=_headers(cliente)).status_code == 403
    assert client.get("/api/v1/contratos", headers=_headers(cliente)).status_code == 403


# --- O auditor mantém acesso total ---


def test_auditor_continua_criando_edificacao(auditor):
    response = client.post(
        "/api/v1/edificacoes",
        json={"nome": f"Ed. Auditor {uuid.uuid4()}", "endereco": "Rua do Auditor, 1"},
        headers=_headers(auditor),
    )

    assert response.status_code == 201
    _cleanup(Edificacao, uuid.UUID(response.json()["id"]))
