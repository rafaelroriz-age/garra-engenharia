"""Regras de negócio e enums de Ocorrência (BL-14, RF-04, RN-03, RN-05, RN-10).

Testes marcados "LACUNA" falham até a correção em `ocorrencia_service` (ver
`00_docs/projeto/revisao-regras-ocorrencias.md`); os demais fixam regras já impostas.
"""
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
    email = f"regras-{uuid.uuid4()}@garra-engenharia.com.br"
    async with _TestSessionLocal() as session:
        usuario = Usuario(nome="Teste BL-14", email=email, senha_hash=hash_password("senha-forte"), ativo=True)
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
async def ctx(db_session):
    """Inspeção + dois sistemas, cada um com um subsistema (para testar coerência)."""
    edificacao = Edificacao(nome=f"Ed. BL-14 {uuid.uuid4()}", endereco="Rua das Regras, 14")
    fiscal = Responsavel(nome="Eng. Fiscal BL-14", tipo="fiscal", crea="141414-GO")
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
        art_fiscalizacao="ART-014",
    )
    db_session.add(contrato)
    await db_session.commit()
    await db_session.refresh(contrato)

    inspecao = Inspecao(contrato_id=contrato.id, tipo="RFO", status="EM_ANDAMENTO")
    outra_inspecao = Inspecao(contrato_id=contrato.id, tipo="RFO", status="EM_ANDAMENTO")
    db_session.add_all([inspecao, outra_inspecao])
    await db_session.commit()
    await db_session.refresh(inspecao)
    await db_session.refresh(outra_inspecao)

    sistema = SistemaPredial(nome=f"Sistema A BL-14 {uuid.uuid4()}", ordem=10)
    outro_sistema = SistemaPredial(nome=f"Sistema B BL-14 {uuid.uuid4()}", ordem=11)
    db_session.add_all([sistema, outro_sistema])
    await db_session.flush()

    subsistema = Subsistema(sistema_id=sistema.id, nome="Sub A", ordem=1)
    subsistema_outro = Subsistema(sistema_id=outro_sistema.id, nome="Sub B", ordem=1)
    db_session.add_all([subsistema, subsistema_outro])
    await db_session.commit()
    for obj in (sistema, outro_sistema, subsistema, subsistema_outro):
        await db_session.refresh(obj)

    yield {
        "inspecao": inspecao,
        "outra_inspecao": outra_inspecao,
        "sistema": sistema,
        "subsistema": subsistema,
        "subsistema_outro": subsistema_outro,
    }

    await db_session.execute(
        delete(Ocorrencia).where(Ocorrencia.inspecao_id.in_([inspecao.id, outra_inspecao.id]))
    )
    for obj in (inspecao, outra_inspecao, contrato, fiscal, subsistema, subsistema_outro, sistema, outro_sistema, edificacao):
        await db_session.delete(obj)
    await db_session.commit()


def _payload(ctx, **sobrescritas):
    payload = {
        "inspecao_id": str(ctx["inspecao"].id),
        "sistema_id": str(ctx["sistema"].id),
        "subsistema_id": str(ctx["subsistema"].id),
        "situacao": "NAO_CONFORME",
        "classificacao": "ANOMALIA",
        "tipo_anomalia": "Fissura",
        "grau_risco": "MEDIO",
    }
    payload.update(sobrescritas)
    return payload


def _post(ctx, auth, inspecao_id=None, **sobrescritas):
    return client.post(
        f"/api/v1/inspecoes/{inspecao_id or ctx['inspecao'].id}/ocorrencias",
        json=_payload(ctx, **sobrescritas),
        headers={"Authorization": auth["Authorization"]},
    )


def _tipo(response) -> str:
    return str(response.json().get("type", ""))


# --- Regras já impostas (regressão) ----------------------------------------


def test_anomalia_exige_tipo_anomalia(auth, ctx):
    r = _post(ctx, auth, tipo_anomalia=None)
    assert r.status_code == 422
    assert "ocorrencia-tipo-anomalia-obrigatorio" in _tipo(r)


def test_falha_exige_tipo_falha(auth, ctx):
    r = _post(ctx, auth, classificacao="FALHA", tipo_anomalia=None, tipo_falha=None)
    assert r.status_code == 422
    assert "ocorrencia-tipo-falha-obrigatorio" in _tipo(r)


def test_grau_risco_invalido_e_rejeitado(auth, ctx):
    r = _post(ctx, auth, grau_risco="ALTO")
    assert r.status_code == 422
    assert "ocorrencia-grau-risco-invalido" in _tipo(r)


def test_prioridade_acima_de_5_e_rejeitada(auth, ctx):
    r = _post(ctx, auth, prioridade=6)
    assert r.status_code == 422
    assert "ocorrencia-prioridade-invalida" in _tipo(r)


def test_nao_se_aplica_gera_prioridade_zero(auth, ctx):
    r = _post(ctx, auth, classificacao="NAO_SE_APLICA", tipo_anomalia=None)
    assert r.status_code == 201
    assert r.json()["prioridade"] == 0


# --- LACUNAS ----------------------------------------------------------------


def test_lacuna_situacao_fora_do_enum_e_rejeitada(auth, ctx):
    r = _post(ctx, auth, situacao="TALVEZ")
    assert r.status_code == 422
    assert "ocorrencia-situacao-invalida" in _tipo(r)


def test_lacuna_classificacao_fora_do_enum_e_rejeitada(auth, ctx):
    r = _post(ctx, auth, classificacao="QUALQUER", tipo_anomalia=None)
    assert r.status_code == 422
    assert "ocorrencia-classificacao-invalida" in _tipo(r)


def test_lacuna_subsistema_de_outro_sistema_e_rejeitado(auth, ctx):
    r = _post(ctx, auth, subsistema_id=str(ctx["subsistema_outro"].id))
    assert r.status_code == 422
    assert "ocorrencia-subsistema-incoerente" in _tipo(r)


def test_lacuna_sistema_inexistente_retorna_404(auth, ctx):
    r = _post(ctx, auth, sistema_id=str(uuid.uuid4()), subsistema_id=None)
    assert r.status_code == 404
    assert "sistema-nao-encontrado" in _tipo(r)


def test_lacuna_subsistema_inexistente_retorna_404(auth, ctx):
    r = _post(ctx, auth, subsistema_id=str(uuid.uuid4()))
    assert r.status_code == 404
    assert "subsistema-nao-encontrado" in _tipo(r)


def test_lacuna_inspecao_inexistente_retorna_404(auth, ctx):
    r = _post(ctx, auth, inspecao_id=uuid.uuid4())
    assert r.status_code == 404
    assert "inspecao-nao-encontrada" in _tipo(r)


def test_lacuna_atualizar_preserva_inspecao_e_seq_numero(auth, ctx):
    criada = _post(ctx, auth).json()
    r = client.put(
        f"/api/v1/ocorrencias/{criada['id']}",
        json=_payload(ctx, inspecao_id=str(ctx["outra_inspecao"].id), descricao="editada"),
        headers={"Authorization": auth["Authorization"]},
    )
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["descricao"] == "editada"
    assert corpo["inspecao_id"] == criada["inspecao_id"]
    assert corpo["seq_numero"] == criada["seq_numero"]


def test_lacuna_filtro_sistema_id_invalido_retorna_422(auth, ctx):
    r = client.get(
        f"/api/v1/inspecoes/{ctx['inspecao'].id}/ocorrencias?sistema_id=nao-e-uuid",
        headers={"Authorization": auth["Authorization"]},
    )
    assert r.status_code == 422
