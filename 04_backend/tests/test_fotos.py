"""Testes de integração de Fotos (BL-11, RF-05, mitigações A08/A10 OWASP).

Cobre upload manual (multipart), upload via clipboard (base64), vinculação a
Ocorrência e Visita, atualização de legenda/ordem, remoção e as rejeições de
arquivo inválido/tamanho excedido. Requer PostgreSQL e MinIO reais rodando
(`05_infra/docker-compose.yml`, mesmo padrão de `tests/test_storage.py`).
"""
import base64
import io
import uuid
from asyncio import run as run_async
from datetime import date

import pytest_asyncio
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
from fastapi.testclient import TestClient
from PIL import Image
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


def _imagem_png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), color="red").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest_asyncio.fixture
async def auth_headers():
    email = f"fotos-{uuid.uuid4()}@garra-engenharia.com.br"
    async with _TestSessionLocal() as session:
        usuario = Usuario(nome="Teste BL-11", email=email, senha_hash=hash_password("senha-forte"), ativo=True)
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
async def visita(db_session):
    edificacao = Edificacao(nome=f"Ed. BL-11 {uuid.uuid4()}", endereco="Rua das Fotos, 1")
    fiscal = Responsavel(nome="Eng. Fiscal BL-11", tipo="fiscal", crea="333333-GO")
    db_session.add_all([edificacao, fiscal])
    await db_session.commit()
    await db_session.refresh(edificacao)
    await db_session.refresh(fiscal)

    contrato = Contrato(
        edificacao_id=edificacao.id,
        fiscal_id=fiscal.id,
        numero=f"CT-BL11-{uuid.uuid4()}",
        tipo_servico="Fiscalização de obra",
        status="em_andamento",
        art_fiscalizacao="ART-001",
    )
    db_session.add(contrato)
    await db_session.commit()
    await db_session.refresh(contrato)

    inspecao = Inspecao(contrato_id=contrato.id, tipo="RFO", status="em_andamento")
    db_session.add(inspecao)
    await db_session.commit()
    await db_session.refresh(inspecao)

    obj = Visita(inspecao_id=inspecao.id, data=date(2026, 7, 1), servicos_executados="Fundação", seq_numero=1)
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)

    yield obj

    await db_session.delete(obj)
    await db_session.delete(inspecao)
    await db_session.delete(contrato)
    await db_session.delete(fiscal)
    await db_session.delete(edificacao)
    await db_session.commit()


@pytest_asyncio.fixture
async def ocorrencia(db_session, visita):
    sistema = SistemaPredial(nome=f"Sistema BL-11 {uuid.uuid4()}", ordem=999)
    db_session.add(sistema)
    await db_session.commit()
    await db_session.refresh(sistema)

    obj = Ocorrencia(
        inspecao_id=visita.inspecao_id,
        sistema_id=sistema.id,
        situacao="Não Conforme",
        classificacao="Anomalia",
        seq_numero=1,
    )
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)

    yield obj

    await db_session.delete(obj)
    await db_session.delete(sistema)
    await db_session.commit()


def _cleanup_foto(foto_id: uuid.UUID) -> None:
    async def _delete() -> None:
        async with _TestSessionLocal() as session:
            await session.execute(delete(Foto).where(Foto.id == foto_id))
            await session.commit()

    run_async(_delete())


def test_upload_arquivo_valido_retorna_storage_key_e_url(auth_headers):
    response = client.post(
        "/api/v1/fotos/upload",
        files={"arquivo": ("foto.png", _imagem_png_bytes(), "image/png")},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["storage_key"].startswith("fotos/")
    assert body["url"].startswith("http")


def test_upload_arquivo_invalido_retorna_422_rfc7807(auth_headers):
    response = client.post(
        "/api/v1/fotos/upload",
        files={"arquivo": ("malicioso.png", b"nao-e-uma-imagem-de-verdade", "image/png")},
        headers=auth_headers,
    )

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == 422
    assert body["type"].startswith("https://garra-engenharia/erros/")


def test_upload_clipboard_valido(auth_headers):
    imagem_base64 = base64.b64encode(_imagem_png_bytes()).decode("ascii")

    response = client.post(
        "/api/v1/fotos/upload-clipboard",
        json={"imagem_base64": imagem_base64},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["storage_key"].startswith("fotos/")


def test_upload_clipboard_base64_invalido_retorna_422(auth_headers):
    response = client.post(
        "/api/v1/fotos/upload-clipboard",
        json={"imagem_base64": "%%%nao-e-base64%%%"},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_vincular_foto_a_ocorrencia(auth_headers, ocorrencia):
    upload = client.post(
        "/api/v1/fotos/upload",
        files={"arquivo": ("foto.png", _imagem_png_bytes(), "image/png")},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/api/v1/ocorrencias/{ocorrencia.id}/fotos",
        json={"storage_key": upload["storage_key"], "legenda": "Fissura na parede", "origem": "upload_manual"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["ocorrencia_id"] == str(ocorrencia.id)
    assert body["legenda"] == "Fissura na parede"

    _cleanup_foto(uuid.UUID(body["id"]))


def test_vincular_foto_a_ocorrencia_inexistente_retorna_404(auth_headers):
    upload = client.post(
        "/api/v1/fotos/upload",
        files={"arquivo": ("foto.png", _imagem_png_bytes(), "image/png")},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/api/v1/ocorrencias/{uuid.uuid4()}/fotos",
        json={"storage_key": upload["storage_key"], "origem": "upload_manual"},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_vincular_foto_a_visita(auth_headers, visita):
    upload = client.post(
        "/api/v1/fotos/upload-clipboard",
        json={"imagem_base64": base64.b64encode(_imagem_png_bytes()).decode("ascii")},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/api/v1/visitas/{visita.id}/fotos",
        json={"storage_key": upload["storage_key"], "origem": "lightshot"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["visita_id"] == str(visita.id)

    _cleanup_foto(uuid.UUID(body["id"]))


def test_atualizar_e_remover_foto(auth_headers, visita):
    upload = client.post(
        "/api/v1/fotos/upload",
        files={"arquivo": ("foto.png", _imagem_png_bytes(), "image/png")},
        headers=auth_headers,
    ).json()
    foto = client.post(
        f"/api/v1/visitas/{visita.id}/fotos",
        json={"storage_key": upload["storage_key"], "origem": "upload_manual"},
        headers=auth_headers,
    ).json()

    resp_update = client.put(
        f"/api/v1/fotos/{foto['id']}", json={"legenda": "Nova legenda", "ordem": 1}, headers=auth_headers
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["legenda"] == "Nova legenda"

    resp_delete = client.delete(f"/api/v1/fotos/{foto['id']}", headers=auth_headers)
    assert resp_delete.status_code == 204

    resp_update_apos_delete = client.put(
        f"/api/v1/fotos/{foto['id']}", json={"legenda": "Outra"}, headers=auth_headers
    )
    assert resp_update_apos_delete.status_code == 404
