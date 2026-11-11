"""Testes do endpoint de emissão do RFO (BL-13): `POST /inspecoes/{id}/relatorios/rfo`.

Storage e renderizador são fakes (sem MinIO nem WeasyPrint). Os testes de
integração exigem o PostgreSQL de 05_infra/docker-compose.yml (localhost:5433);
os de unidade (versão, chave, 503 sem WeasyPrint, 401 sem token) não usam banco.
"""
import builtins
import uuid
from datetime import date

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.v1.relatorios import get_renderizador_rfo
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Contrato, Edificacao, Foto, Inspecao, Relatorio, Responsavel, Usuario, Visita
from app.services.relatorio_service import (
    GeradorIndisponivelError,
    RenderizadorRFOPadrao,
    chave_relatorio,
    proxima_versao,
)
from app.services.storage import ObjectNotFoundError, StorageClient, get_storage_client

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


class FakeStorage(StorageClient):
    def __init__(self, objetos: dict[str, bytes] | None = None) -> None:
        self.objetos: dict[str, bytes] = dict(objetos or {})
        self.content_types: dict[str, str] = {}

    def upload(self, key, file_bytes, content_type, *, max_size_bytes=None):
        self.objetos[key] = file_bytes
        self.content_types[key] = content_type
        return key

    def download(self, key):
        if key not in self.objetos:
            raise ObjectNotFoundError(key)
        return self.objetos[key]

    def exists(self, key):
        return key in self.objetos

    def delete(self, key):
        self.objetos.pop(key, None)

    def list_keys(self, prefix=""):
        return [k for k in self.objetos if k.startswith(prefix)]

    def generate_presigned_url(self, key, expires_in):
        return f"https://storage.test/{key}?expires={expires_in}"


class FakeRenderizador:
    def __init__(self) -> None:
        self.chamadas: list[tuple[str, dict, dict]] = []

    def gerar_pdf(self, contexto, fotos_bytes):
        self.chamadas.append(("pdf", contexto, fotos_bytes))
        return b"%PDF-1.7 fake"

    def gerar_docx(self, contexto, fotos_bytes):
        self.chamadas.append(("docx", contexto, fotos_bytes))
        return b"PK fake docx"


FOTO_KEY = "fotos/teste-bl13.jpg"


@pytest.fixture
def api():
    storage = FakeStorage({FOTO_KEY: b"\xff\xd8 jpeg"})
    renderizador = FakeRenderizador()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_storage_client] = lambda: storage
    app.dependency_overrides[get_renderizador_rfo] = lambda: renderizador
    yield TestClient(app), storage, renderizador
    app.dependency_overrides.pop(get_storage_client, None)
    app.dependency_overrides.pop(get_renderizador_rfo, None)


def _auth(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario.id))}"}


@pytest_asyncio.fixture
async def cenario():
    sufixo = uuid.uuid4().hex[:8]
    async with _TestSessionLocal() as s:
        usuarios = {
            role: Usuario(
                nome=f"{role} BL-13",
                email=f"{role}-bl13-{sufixo}@garra.com",
                senha_hash=hash_password("senha-forte-123"),
                ativo=True,
                role=role,
            )
            for role in ("auditor", "auxiliar", "cliente")
        }
        s.add_all(usuarios.values())
        await s.commit()

        contratante = Responsavel(nome="Contratante BL-13", tipo="sindico", usuario_id=usuarios["cliente"].id)
        fiscal = Responsavel(nome="Fiscal BL-13", tipo="fiscal", crea="123-GO")
        edificacao = Edificacao(nome=f"Ed. BL-13 {sufixo}", endereco="Rua RFO, 1")
        s.add_all([contratante, fiscal, edificacao])
        await s.commit()

        contrato = Contrato(
            edificacao_id=edificacao.id,
            fiscal_id=fiscal.id,
            contratante_id=contratante.id,
            numero=f"CT-BL13-{sufixo}",
            tipo_servico="Fiscalização",
            status="em_andamento",
            data_inicio=date(2026, 1, 5),
            objeto="Reforma BL-13",
            prazo_dias=60,
            art_fiscalizacao="ART-BL13",
        )
        s.add(contrato)
        await s.commit()

        rfo = Inspecao(contrato_id=contrato.id, tipo="RFO", status="em_andamento")
        ltip = Inspecao(contrato_id=contrato.id, tipo="LTIP", status="em_andamento")
        s.add_all([rfo, ltip])
        await s.commit()

        visita = Visita(inspecao_id=rfo.id, data=date(2026, 1, 15), servicos_executados="Concretagem", seq_numero=1)
        s.add(visita)
        await s.commit()
        s.add(Foto(visita_id=visita.id, storage_key=FOTO_KEY, origem="upload", legenda="Laje", ordem=1))
        await s.commit()

        yield {"usuarios": usuarios, "rfo_id": rfo.id, "ltip_id": ltip.id}

        inspecoes = [rfo.id, ltip.id]
        await s.execute(delete(Relatorio).where(Relatorio.inspecao_id.in_(inspecoes)))
        await s.execute(delete(Foto).where(Foto.visita_id == visita.id))
        await s.execute(delete(Visita).where(Visita.id == visita.id))
        await s.execute(delete(Inspecao).where(Inspecao.id.in_(inspecoes)))
        await s.execute(delete(Contrato).where(Contrato.id == contrato.id))
        await s.execute(delete(Edificacao).where(Edificacao.id == edificacao.id))
        await s.execute(delete(Responsavel).where(Responsavel.id.in_([contratante.id, fiscal.id])))
        await s.execute(delete(Usuario).where(Usuario.id.in_([u.id for u in usuarios.values()])))
        await s.commit()


def _url(inspecao_id) -> str:
    return f"/api/v1/inspecoes/{inspecao_id}/relatorios/rfo"


# --- unidade (sem banco) -------------------------------------------------------


def test_proxima_versao_incrementa_e_ignora_fora_do_padrao():
    assert proxima_versao([]) == "V01"
    assert proxima_versao(["V01", "V09", "rascunho", ""]) == "V10"


def test_chave_relatorio_e_deterministica():
    inspecao_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    assert chave_relatorio(inspecao_id, "V02", "pdf") == f"relatorios/{inspecao_id}/rfo-v02.pdf"


def test_renderizador_padrao_sem_weasyprint_vira_503(monkeypatch):
    import_original = builtins.__import__

    def _import(nome, globals_=None, locals_=None, fromlist=(), level=0):
        if nome == "app.services.report_generator" and fromlist and "rfo_pipeline" in fromlist:
            raise OSError("cannot load library 'libpango-1.0'")
        return import_original(nome, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _import)
    with pytest.raises(GeradorIndisponivelError) as exc:
        RenderizadorRFOPadrao().gerar_pdf({}, {})
    assert exc.value.status_code == 503
    assert exc.value.type_suffix == "gerador-relatorio-indisponivel"


def test_sem_token_retorna_401(api):
    client, _storage, renderizador = api
    response = client.post(_url(uuid.uuid4()))
    assert response.status_code == 401
    assert renderizador.chamadas == []


# --- integração (PostgreSQL) -----------------------------------------------------


def test_auditor_emite_rfo_201_e_grava_pdf_docx(api, cenario):
    client, storage, renderizador = api
    rfo_id = cenario["rfo_id"]

    response = client.post(_url(rfo_id), headers=_auth(cenario["usuarios"]["auditor"]))

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["inspecao_id"] == str(rfo_id)
    assert (body["tipo"], body["versao"], body["status"]) == ("RFO", "V01", "emitido")
    assert body["tem_pdf"] is True and body["tem_docx"] is True
    assert body["criado_em"]
    assert "pdf_key" not in body
    pdf_key, docx_key = f"relatorios/{rfo_id}/rfo-v01.pdf", f"relatorios/{rfo_id}/rfo-v01.docx"
    assert storage.objetos[pdf_key] == b"%PDF-1.7 fake"
    assert storage.objetos[docx_key] == b"PK fake docx"
    assert storage.content_types[pdf_key] == "application/pdf"
    # O renderizador recebe o contexto do banco e os bytes da foto da visita.
    formato, contexto, fotos = renderizador.chamadas[0]
    assert formato == "pdf"
    assert contexto["visitas"][0]["fotos"][0]["storage_key"] == FOTO_KEY
    assert fotos == {FOTO_KEY: b"\xff\xd8 jpeg"}


def test_segunda_emissao_incrementa_versao_e_preserva_a_anterior(api, cenario):
    client, storage, _ = api
    rfo_id = cenario["rfo_id"]
    headers = _auth(cenario["usuarios"]["auditor"])

    primeira = client.post(_url(rfo_id), headers=headers).json()
    segunda = client.post(_url(rfo_id), headers=headers)

    assert primeira["versao"] == "V01"
    assert segunda.status_code == 201
    assert segunda.json()["versao"] == "V02"
    assert segunda.json()["id"] != primeira["id"]
    for versao in ("v01", "v02"):
        assert f"relatorios/{rfo_id}/rfo-{versao}.pdf" in storage.objetos
        assert f"relatorios/{rfo_id}/rfo-{versao}.docx" in storage.objetos


@pytest.mark.parametrize("role", ["auxiliar", "cliente"])
def test_auxiliar_e_cliente_recebem_403(api, cenario, role):
    client, _storage, renderizador = api
    response = client.post(_url(cenario["rfo_id"]), headers=_auth(cenario["usuarios"][role]))
    assert response.status_code == 403
    assert response.json()["type"].endswith("/acesso-negado")
    assert renderizador.chamadas == []


def test_inspecao_inexistente_retorna_404(api, cenario):
    client, _, _ = api
    response = client.post(_url(uuid.uuid4()), headers=_auth(cenario["usuarios"]["auditor"]))
    assert response.status_code == 404
    assert response.json()["type"].endswith("/inspecao-nao-encontrada")


def test_inspecao_nao_rfo_retorna_409(api, cenario):
    client, storage, _ = api
    response = client.post(_url(cenario["ltip_id"]), headers=_auth(cenario["usuarios"]["auditor"]))
    assert response.status_code == 409
    assert response.json()["type"].endswith("/inspecao-nao-rfo")
    assert not any(k.startswith("relatorios/") for k in storage.objetos)


def test_payload_com_campo_extra_retorna_422(api, cenario):
    client, _, _ = api
    response = client.post(
        _url(cenario["rfo_id"]),
        headers=_auth(cenario["usuarios"]["auditor"]),
        json={"pdf_key": "relatorios/outro/arquivo.pdf"},
    )
    assert response.status_code == 422


def test_foto_ausente_no_storage_retorna_409_sem_gravar(api, cenario):
    client, storage, renderizador = api
    storage.objetos.pop(FOTO_KEY)
    response = client.post(_url(cenario["rfo_id"]), headers=_auth(cenario["usuarios"]["auditor"]))
    assert response.status_code == 409
    assert response.json()["type"].endswith("/foto-ausente-no-storage")
    assert renderizador.chamadas == []


def test_cliente_do_contrato_ve_relatorio_emitido_no_portal(api, cenario):
    client, _, _ = api
    emitido = client.post(_url(cenario["rfo_id"]), headers=_auth(cenario["usuarios"]["auditor"])).json()

    response = client.get("/api/v1/portal/relatorios", headers=_auth(cenario["usuarios"]["cliente"]))

    assert response.status_code == 200
    relatorio = next(r for r in response.json() if r["id"] == emitido["id"])
    assert (relatorio["tipo"], relatorio["versao"]) == ("RFO", "V01")
    assert relatorio["tem_pdf"] is True and relatorio["tem_docx"] is True

    download = client.get(
        f"/api/v1/portal/relatorios/{emitido['id']}/download/pdf",
        headers=_auth(cenario["usuarios"]["cliente"]),
    )
    assert download.status_code == 200
    assert f"relatorios/{cenario['rfo_id']}/rfo-v01.pdf" in download.json()["url"]
