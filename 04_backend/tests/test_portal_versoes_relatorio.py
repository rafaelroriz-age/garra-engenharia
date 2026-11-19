"""Diagnóstico: versões de relatório (V01, V02…) no Portal do Cliente (DEC-48 P1).

Cada emissão cria um `Relatorio` novo. Estes testes fixam o comportamento atual
da listagem/download do portal quando uma inspeção tem mais de uma versão, sem
alterar código de produção. Onde o comportamento atual contraria o esperado, o
teste está marcado com `xfail(strict=True)` (ver 00_docs/backlog-auto/portal-versoes-relatorio.md).
"""
import uuid
from datetime import UTC, date, datetime

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Contrato, Edificacao, Inspecao, Relatorio, Responsavel, Usuario
from app.services.storage import get_storage_client

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


class _FakeStorage:
    """Storage falso: URL pré-assinada determinística, sem rede."""

    def generate_presigned_url(self, key: str, expires_in: int = 900) -> str:
        return f"https://storage.test/assinada/{uuid.uuid4().hex}?X-Expires={expires_in}"


@pytest.fixture(autouse=True)
def _overrides():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_storage_client] = lambda: _FakeStorage()
    yield
    app.dependency_overrides.pop(get_storage_client, None)


client = TestClient(app)


def _auth(usuario_id) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario_id))}"}


@pytest_asyncio.fixture
async def cenario():
    """Cliente A com inspeção que tem RFO V01 e V02; cliente B sem nenhum relatório."""
    sufixo = uuid.uuid4().hex[:8]
    async with _TestSessionLocal() as s:
        user_a = Usuario(nome="Cliente A", email=f"ver-a-{sufixo}@garra.com",
                         senha_hash=hash_password("senha-forte-123"), ativo=True, role="cliente")
        user_b = Usuario(nome="Cliente B", email=f"ver-b-{sufixo}@garra.com",
                         senha_hash=hash_password("senha-forte-123"), ativo=True, role="cliente")
        s.add_all([user_a, user_b])
        await s.commit()

        resp_a = Responsavel(nome="Contratante A", tipo="sindico", usuario_id=user_a.id)
        resp_b = Responsavel(nome="Contratante B", tipo="sindico", usuario_id=user_b.id)
        s.add_all([resp_a, resp_b])
        await s.commit()

        edif = Edificacao(nome=f"Ed. Versoes {sufixo}", endereco="Rua das Versões")
        s.add(edif)
        await s.commit()

        contrato = Contrato(edificacao_id=edif.id, fiscal_id=resp_a.id, contratante_id=resp_a.id,
                            numero=f"CT-VER-{sufixo}", tipo_servico="ltip",
                            status="em_andamento", data_inicio=date(2026, 1, 10))
        s.add(contrato)
        await s.commit()

        inspecao = Inspecao(contrato_id=contrato.id, tipo="ltip", status="em_andamento")
        s.add(inspecao)
        await s.commit()

        v01 = Relatorio(inspecao_id=inspecao.id, versao="V01", tipo="rfo", status="emitido",
                        pdf_key=f"relatorios/{sufixo}/V01.pdf", docx_key=f"relatorios/{sufixo}/V01.docx",
                        emitido_em=datetime(2026, 2, 1, tzinfo=UTC))
        v02 = Relatorio(inspecao_id=inspecao.id, versao="V02", tipo="rfo", status="emitido",
                        pdf_key=f"relatorios/{sufixo}/V02.pdf", docx_key=f"relatorios/{sufixo}/V02.docx",
                        emitido_em=datetime(2026, 3, 1, tzinfo=UTC))
        s.add_all([v01, v02])
        await s.commit()

        yield {"user_a": user_a, "user_b": user_b, "inspecao_id": inspecao.id,
               "v01": v01, "v02": v02, "sufixo": sufixo}

        await s.execute(delete(Relatorio).where(Relatorio.inspecao_id == inspecao.id))
        await s.execute(delete(Inspecao).where(Inspecao.id == inspecao.id))
        await s.execute(delete(Contrato).where(Contrato.id == contrato.id))
        await s.execute(delete(Edificacao).where(Edificacao.id == edif.id))
        await s.execute(delete(Responsavel).where(Responsavel.id.in_([resp_a.id, resp_b.id])))
        await s.execute(delete(Usuario).where(Usuario.id.in_([user_a.id, user_b.id])))
        await s.commit()


# (a) listagem com V01 e V02 -------------------------------------------------

def test_listagem_retorna_todas_as_versoes_da_inspecao(cenario):
    r = client.get("/api/v1/portal/relatorios", headers=_auth(cenario["user_a"].id))

    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert {item["versao"] for item in body} == {"V01", "V02"}
    assert {item["inspecao_id"] for item in body} == {str(cenario["inspecao_id"])}


def test_listagem_ordena_da_emissao_mais_recente_para_a_mais_antiga(cenario):
    r = client.get("/api/v1/portal/relatorios", headers=_auth(cenario["user_a"].id))

    assert [item["versao"] for item in r.json()] == ["V02", "V01"]


def test_listagem_expoe_o_campo_versao_e_flags_de_arquivo(cenario):
    item = client.get("/api/v1/portal/relatorios", headers=_auth(cenario["user_a"].id)).json()[0]

    assert item["versao"] == "V02"
    assert item["tem_pdf"] is True
    assert item["tem_docx"] is True


def test_listagem_sinaliza_qual_versao_e_a_vigente(cenario):
    body = client.get("/api/v1/portal/relatorios", headers=_auth(cenario["user_a"].id)).json()

    flags = [item.get("vigente", item.get("mais_recente")) for item in body]
    assert flags == [True, False]


@pytest.mark.asyncio
async def test_cada_tipo_tem_sua_propria_versao_vigente(cenario):
    async with _TestSessionLocal() as s:
        outro = Relatorio(inspecao_id=cenario["inspecao_id"], versao="V01", tipo="rfa",
                          status="emitido", pdf_key=None, docx_key=None,
                          emitido_em=datetime(2026, 1, 1, tzinfo=UTC))
        s.add(outro)
        await s.commit()

    body = client.get("/api/v1/portal/relatorios", headers=_auth(cenario["user_a"].id)).json()
    vig = {(i["tipo"], i["versao"]): i["vigente"] for i in body}
    assert vig == {("rfo", "V02"): True, ("rfo", "V01"): False, ("rfa", "V01"): True}


@pytest.mark.asyncio
async def test_relatorio_com_uma_so_versao_e_vigente(cenario):
    async with _TestSessionLocal() as s:
        await s.execute(delete(Relatorio).where(Relatorio.id == cenario["v01"].id))
        await s.commit()

    body = client.get("/api/v1/portal/relatorios", headers=_auth(cenario["user_a"].id)).json()
    assert [(i["versao"], i["vigente"]) for i in body] == [("V02", True)]


# (b) isolamento entre contratantes --------------------------------------------

def test_outro_contratante_nao_ve_nenhuma_versao(cenario):
    r = client.get("/api/v1/portal/relatorios", headers=_auth(cenario["user_b"].id))

    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.parametrize("versao", ["v01", "v02"])
@pytest.mark.parametrize("formato", ["pdf", "docx"])
def test_outro_contratante_nao_baixa_nenhuma_versao(cenario, versao, formato):
    relatorio = cenario[versao]

    r = client.get(
        f"/api/v1/portal/relatorios/{relatorio.id}/download/{formato}",
        headers=_auth(cenario["user_b"].id),
    )

    assert r.status_code == 404
    assert r.json()["type"].endswith("/relatorio-nao-encontrado")


# (c) download devolve URL pré-assinada, nunca a chave -------------------------

@pytest.mark.parametrize("versao", ["v01", "v02"])
@pytest.mark.parametrize("formato", ["pdf", "docx"])
def test_download_devolve_url_pre_assinada_e_nunca_a_chave(cenario, versao, formato):
    relatorio = cenario[versao]
    chave = getattr(relatorio, f"{formato}_key")

    r = client.get(
        f"/api/v1/portal/relatorios/{relatorio.id}/download/{formato}",
        headers=_auth(cenario["user_a"].id),
    )

    assert r.status_code == 200
    body = r.json()
    assert body["relatorio_id"] == str(relatorio.id)
    assert body["formato"] == formato
    assert body["url"].startswith("https://")
    assert body["expira_em_segundos"] == 900
    assert chave not in r.text
    assert "pdf_key" not in r.text and "docx_key" not in r.text


def test_listagem_nao_vaza_chaves_de_storage(cenario):
    r = client.get("/api/v1/portal/relatorios", headers=_auth(cenario["user_a"].id))

    assert "relatorios/" not in r.text
    assert "pdf_key" not in r.text and "docx_key" not in r.text


# (d) relatório sem arquivos ---------------------------------------------------

@pytest.mark.asyncio
async def test_relatorio_sem_pdf_key_nem_docx_key_nao_gera_download(cenario):
    async with _TestSessionLocal() as s:
        vazio = Relatorio(inspecao_id=cenario["inspecao_id"], versao="V03", tipo="rfo",
                          status="rascunho", pdf_key=None, docx_key=None, emitido_em=None)
        s.add(vazio)
        await s.commit()
        vazio_id = vazio.id

    headers = _auth(cenario["user_a"].id)
    item = next(i for i in client.get("/api/v1/portal/relatorios", headers=headers).json()
                if i["id"] == str(vazio_id))
    assert item["tem_pdf"] is False and item["tem_docx"] is False

    for formato in ("pdf", "docx"):
        r = client.get(f"/api/v1/portal/relatorios/{vazio_id}/download/{formato}", headers=headers)
        assert r.status_code == 404
        assert r.json()["type"].endswith("/arquivo-nao-disponivel")


def test_formato_invalido_retorna_404(cenario):
    r = client.get(
        f"/api/v1/portal/relatorios/{cenario['v01'].id}/download/exe",
        headers=_auth(cenario["user_a"].id),
    )

    assert r.status_code == 404
    assert r.json()["type"].endswith("/formato-nao-suportado")
