import uuid
from asyncio import run as run_async

import pytest_asyncio
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Contrato, Edificacao, Responsavel, Usuario
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


async def _limpar_usuario_e_dependencias(usuario_id: uuid.UUID) -> None:
    async with _TestSessionLocal() as session:
        await session.execute(delete(Contrato).where(Contrato.fiscal_id == usuario_id))
        await session.execute(delete(Responsavel).where(Responsavel.usuario_id == usuario_id))
        await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
        await session.commit()


async def _criar_usuario(session, *, email: str, role: str = "auditor") -> Usuario:
    usuario = Usuario(
        nome=f"Usuário {role}",
        email=email,
        senha_hash=hash_password("senha-forte-123"),
        ativo=True,
        role=role,
    )
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)
    return usuario


@pytest_asyncio.fixture
async def usuario_auditor():
    async with _TestSessionLocal() as session:
        usuario = await _criar_usuario(session, email=f"auditor-{uuid.uuid4()}@garra.com", role="auditor")
        yield usuario
        await _limpar_usuario_e_dependencias(usuario.id)


@pytest_asyncio.fixture
async def usuario_cliente_sem_responsavel():
    async with _TestSessionLocal() as session:
        usuario = await _criar_usuario(session, email=f"cliente-{uuid.uuid4()}@garra.com", role="cliente")
        yield usuario
        await _limpar_usuario_e_dependencias(usuario.id)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_usuario_auditor_default_pode_acessar_rota_existente(usuario_auditor):
    token = create_access_token(subject=str(usuario_auditor.id))

    response = client.get("/api/v1/auth/me", headers=_auth_header(token))

    assert response.status_code == 200
    assert response.json()["role"] == "auditor"


def test_require_role_bloqueia_usuario_auditor_com_403(usuario_auditor):
    token = create_access_token(subject=str(usuario_auditor.id))

    response = client.get("/api/v1/portal/edificacoes", headers=_auth_header(token))

    assert response.status_code == 403
    assert response.json()["type"].endswith("/acesso-negado")


@pytest_asyncio.fixture
async def dados_portal():
    async with _TestSessionLocal() as session:
        contratante_usuario = await _criar_usuario(session, email=f"contratante-{uuid.uuid4()}@garra.com", role="cliente")
        outro_usuario = await _criar_usuario(session, email=f"outro-{uuid.uuid4()}@garra.com", role="cliente")

        contratante = Responsavel(nome="Contratante Teste", tipo="sindico", usuario_id=contratante_usuario.id)
        outro_contratante = Responsavel(nome="Outro Contratante", tipo="sindico", usuario_id=outro_usuario.id)
        session.add_all([contratante, outro_contratante])
        await session.commit()
        await session.refresh(contratante)
        await session.refresh(outro_contratante)

        edificacao_do_contratante = Edificacao(nome="Edifício Cliente", endereco="Rua do Cliente")
        edificacao_de_outro = Edificacao(nome="Edifício Outro", endereco="Rua do Outro")
        session.add_all([edificacao_do_contratante, edificacao_de_outro])
        await session.commit()
        await session.refresh(edificacao_do_contratante)
        await session.refresh(edificacao_de_outro)

        contrato_do_contratante = Contrato(
            edificacao_id=edificacao_do_contratante.id,
            fiscal_id=contratante.id,
            contratante_id=contratante.id,
            numero="CT-01",
            tipo_servico="fiscalizacao",
            status="em_andamento",
        )
        contrato_de_outro = Contrato(
            edificacao_id=edificacao_de_outro.id,
            fiscal_id=outro_contratante.id,
            contratante_id=outro_contratante.id,
            numero="CT-02",
            tipo_servico="fiscalizacao",
            status="em_andamento",
        )
        session.add_all([contrato_do_contratante, contrato_de_outro])
        await session.commit()

        yield {
            "usuario": contratante_usuario,
            "responsavel": contratante,
            "edificacao_id": edificacao_do_contratante.id,
            "outra_edificacao_id": edificacao_de_outro.id,
        }

        await session.execute(delete(Contrato).where(Contrato.numero.in_(["CT-01", "CT-02"])))
        await session.execute(delete(Edificacao).where(Edificacao.id.in_([edificacao_do_contratante.id, edificacao_de_outro.id])))
        await session.execute(delete(Responsavel).where(Responsavel.id.in_([contratante.id, outro_contratante.id])))
        await session.execute(delete(Usuario).where(Usuario.id.in_([contratante_usuario.id, outro_usuario.id])))
        await session.commit()


def test_get_portal_edificacoes_retorna_apenas_as_do_contratante(dados_portal):
    token = create_access_token(subject=str(dados_portal["usuario"].id))

    response = client.get("/api/v1/portal/edificacoes", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(dados_portal["edificacao_id"])


def test_cliente_sem_responsavel_vinculado_recebe_404_em_portal(usuario_cliente_sem_responsavel):
    token = create_access_token(subject=str(usuario_cliente_sem_responsavel.id))

    response = client.get("/api/v1/portal/edificacoes", headers=_auth_header(token))

    assert response.status_code == 404
    assert response.json()["type"].endswith("/recurso-nao-encontrado")
