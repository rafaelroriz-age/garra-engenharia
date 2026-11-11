"""Testes da emissão genérica por tipo (V1-02).

`POST /inspecoes/{id}/relatorios/{tipo}`, `GET /inspecoes/{id}/relatorios` e
`GET /inspecoes/{id}/relatorios/{relatorio_id}/download/{formato}`, além do
registro de emissores (`relatorio_service.EMISSORES`). Storage e renderizador
são fakes (sem MinIO nem WeasyPrint); os testes de integração exigem o
PostgreSQL de 05_infra/docker-compose.yml (localhost:5433).
"""
import io
import uuid
from datetime import date

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.v1.relatorios import get_renderizador_por_tipo, get_renderizador_rfo
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Contrato, Edificacao, Foto, Inspecao, Relatorio, Responsavel, Usuario, Visita
from app.services import relatorio_service
from app.services.relatorio_service import (
    EMISSORES,
    ContextoIncompletoError,
    Emissor,
    Renderizador,
    RfoContextoIncompletoError,
    chave_relatorio,
    obter_emissor,
    registrar_emissor,
)
from app.services.report_generator import rfo_contexto
from app.services.report_generator.imagem import otimizar_imagem
from app.services.storage import get_storage_client
from tests.test_relatorios_rfo_api import FakeRenderizador, FakeStorage

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)

FOTO_RFO = "fotos/teste-v102-rfo.jpg"
FOTO_TESTE = "fotos/teste-v102-teste.jpg"


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


def _auth(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario.id))}"}


async def _contexto_teste(db, inspecao_id):
    tipo = (await db.execute(select(Inspecao.tipo).where(Inspecao.id == inspecao_id))).scalar_one()
    return {"inspecao": {"id": str(inspecao_id), "tipo": tipo}, "fotos": [FOTO_TESTE], "titulo": None}


@pytest.fixture
def emissor_teste():
    """Registra o tipo fake 'TESTE' só durante o teste."""
    emissor = registrar_emissor(
        "teste",
        Emissor(
            tipo="TESTE",
            montar_contexto=_contexto_teste,
            validar_contexto=lambda ctx: [],
            extrair_fotos=lambda ctx: set(ctx["fotos"]),
            pipeline="pipeline_que_nao_existe",
        ),
    )
    yield emissor
    EMISSORES.pop("TESTE", None)


@pytest.fixture
def api():
    storage = FakeStorage({FOTO_RFO: b"\xff\xd8 rfo", FOTO_TESTE: b"\xff\xd8 teste"})
    renderizador = FakeRenderizador()
    tipos_pedidos: list[str] = []

    def fabrica(tipo):
        tipos_pedidos.append(tipo)
        return renderizador

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_storage_client] = lambda: storage
    app.dependency_overrides[get_renderizador_rfo] = lambda: renderizador
    app.dependency_overrides[get_renderizador_por_tipo] = lambda: fabrica
    yield TestClient(app), storage, renderizador, tipos_pedidos
    for dep in (get_storage_client, get_renderizador_rfo, get_renderizador_por_tipo):
        app.dependency_overrides.pop(dep, None)


@pytest_asyncio.fixture
async def cenario():
    sufixo = uuid.uuid4().hex[:8]
    async with _TestSessionLocal() as s:
        usuarios = {
            role: Usuario(
                nome=f"{role} V1-02",
                email=f"{role}-v102-{sufixo}@garra.com",
                senha_hash=hash_password("senha-forte-123"),
                ativo=True,
                role=role,
            )
            for role in ("auditor", "auxiliar", "cliente")
        }
        s.add_all(usuarios.values())
        await s.commit()

        contratante = Responsavel(nome="Contratante V1-02", tipo="sindico", usuario_id=usuarios["cliente"].id)
        fiscal = Responsavel(nome="Fiscal V1-02", tipo="fiscal", crea="123-GO")
        edificacao = Edificacao(nome=f"Ed. V1-02 {sufixo}", endereco="Rua Genérica, 2")
        s.add_all([contratante, fiscal, edificacao])
        await s.commit()

        # `inspecoes.contrato_id` é UNIQUE (contrato 1:1 inspeção): um contrato por inspeção.
        contratos = {
            tipo: Contrato(
                edificacao_id=edificacao.id,
                fiscal_id=fiscal.id,
                contratante_id=contratante.id,
                numero=f"CT-V102-{tipo}-{sufixo}",
                tipo_servico="Fiscalização",
                status="em_andamento",
                data_inicio=date(2026, 1, 5),
                objeto="Reforma V1-02",
                prazo_dias=60,
                art_fiscalizacao="ART-V102",
            )
            for tipo in ("RFO", "LTIP", "TESTE")
        }
        s.add_all(contratos.values())
        await s.commit()

        rfo = Inspecao(contrato_id=contratos["RFO"].id, tipo="RFO", status="em_andamento")
        ltip = Inspecao(contrato_id=contratos["LTIP"].id, tipo="LTIP", status="em_andamento")
        teste = Inspecao(contrato_id=contratos["TESTE"].id, tipo="TESTE", status="em_andamento")
        s.add_all([rfo, ltip, teste])
        await s.commit()

        visita = Visita(inspecao_id=rfo.id, data=date(2026, 1, 15), servicos_executados="Pintura", seq_numero=1)
        s.add(visita)
        await s.commit()
        s.add(Foto(visita_id=visita.id, storage_key=FOTO_RFO, origem="upload", legenda="Fachada", ordem=1))
        await s.commit()

        yield {"usuarios": usuarios, "rfo_id": rfo.id, "ltip_id": ltip.id, "teste_id": teste.id}

        inspecoes = [rfo.id, ltip.id, teste.id]
        await s.execute(delete(Relatorio).where(Relatorio.inspecao_id.in_(inspecoes)))
        await s.execute(delete(Foto).where(Foto.visita_id == visita.id))
        await s.execute(delete(Visita).where(Visita.id == visita.id))
        await s.execute(delete(Inspecao).where(Inspecao.id.in_(inspecoes)))
        await s.execute(delete(Contrato).where(Contrato.id.in_([c.id for c in contratos.values()])))
        await s.execute(delete(Edificacao).where(Edificacao.id == edificacao.id))
        await s.execute(delete(Responsavel).where(Responsavel.id.in_([contratante.id, fiscal.id])))
        await s.execute(delete(Usuario).where(Usuario.id.in_([u.id for u in usuarios.values()])))
        await s.commit()


def _url(inspecao_id, tipo) -> str:
    return f"/api/v1/inspecoes/{inspecao_id}/relatorios/{tipo}"


# --- unidade (sem banco) -------------------------------------------------------


def test_rfo_registrado_com_contrato_do_emissor():
    emissor = obter_emissor("rfo")
    assert EMISSORES["RFO"] is emissor
    assert emissor.tipo == "RFO"
    assert emissor.montar_contexto is rfo_contexto.montar_contexto_rfo
    assert emissor.validar_contexto is rfo_contexto.validar_contexto_rfo
    assert emissor.pipeline == "rfo_pipeline"
    contexto = {"visitas": [{"fotos": [{"storage_key": "a"}, {"storage_key": "b"}]}, {"fotos": [{"storage_key": "a"}]}]}
    assert emissor.extrair_fotos(contexto) == {"a", "b"}
    assert isinstance(emissor.criar_renderizador(), Renderizador)


def test_registrar_emissor_com_tipo_divergente_falha():
    emissor = obter_emissor("RFO")
    with pytest.raises(ValueError):
        registrar_emissor("LTIP", emissor)
    assert "LTIP" not in EMISSORES


def test_chave_por_tipo_preserva_formato_do_rfo():
    inspecao_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    assert chave_relatorio(inspecao_id, "V03", "pdf") == f"relatorios/{inspecao_id}/rfo-v03.pdf"
    assert chave_relatorio(inspecao_id, "V01", "docx", "LTIP") == f"relatorios/{inspecao_id}/ltip-v01.docx"


def test_erro_de_contexto_incompleto_generico_e_alias_do_rfo():
    erro = ContextoIncompletoError("LTIP", ["contrato.objeto"])
    assert (erro.status_code, erro.type_suffix, erro.tipo) == (422, "ltip-contexto-incompleto", "LTIP")
    rfo = RfoContextoIncompletoError(["fiscal.crea"])
    assert isinstance(rfo, ContextoIncompletoError)
    assert (rfo.type_suffix, rfo.campos_faltantes) == ("rfo-contexto-incompleto", ["fiscal.crea"])


def test_renderizador_generico_usa_modulo_recebido_e_otimiza_fotos():
    import types

    recebidas = {}

    def _gerar_pdf(contexto, fotos, destino):
        recebidas.update(fotos)
        destino.write_bytes(b"%PDF modulo")

    pipeline = types.ModuleType("pipeline_fake")
    pipeline.gerar_pdf = _gerar_pdf
    buffer = io.BytesIO()
    Image.new("RGB", (2400, 1200), "red").save(buffer, format="PNG")

    assert Renderizador(pipeline).gerar_pdf({}, {"foto": buffer.getvalue()}) == b"%PDF modulo"
    assert Image.open(io.BytesIO(recebidas["foto"])).size == (1200, 600)


def test_otimizar_imagem_reexportada_pelo_pacote():
    from app.services import report_generator

    assert report_generator.otimizar_imagem is otimizar_imagem


# --- integração (PostgreSQL) -----------------------------------------------------


def test_tipo_inexistente_retorna_422_com_tipos_disponiveis(api, cenario):
    client, storage, renderizador, _ = api
    response = client.post(_url(cenario["rfo_id"], "inexistente"), headers=_auth(cenario["usuarios"]["auditor"]))
    assert response.status_code == 422
    body = response.json()
    assert body["type"].endswith("/tipo-relatorio-nao-registrado")
    assert "INEXISTENTE" in body["detail"]
    assert "RFO" in body["errors"][0]["disponiveis"]
    assert renderizador.chamadas == []
    assert not any(k.startswith("relatorios/") for k in storage.objetos)


def test_tipo_diferente_da_inspecao_retorna_409(api, cenario):
    client, storage, renderizador, _ = api
    response = client.post(_url(cenario["ltip_id"], "rfo"), headers=_auth(cenario["usuarios"]["auditor"]))
    assert response.status_code == 409
    assert response.json()["type"].endswith("/inspecao-nao-rfo")
    assert renderizador.chamadas == []
    assert not any(k.startswith("relatorios/") for k in storage.objetos)


def test_rota_generica_normaliza_tipo_e_emite_rfo(api, cenario):
    client, storage, _, tipos_pedidos = api
    rfo_id = cenario["rfo_id"]
    response = client.post(_url(rfo_id, "Rfo"), headers=_auth(cenario["usuarios"]["auditor"]))
    assert response.status_code == 201, response.text
    assert (response.json()["tipo"], response.json()["versao"]) == ("RFO", "V01")
    assert tipos_pedidos == ["RFO"]
    assert f"relatorios/{rfo_id}/rfo-v01.pdf" in storage.objetos


def test_auxiliar_nao_emite_pela_rota_generica(api, cenario):
    client, _, renderizador, _ = api
    response = client.post(_url(cenario["rfo_id"], "RFO"), headers=_auth(cenario["usuarios"]["auxiliar"]))
    assert response.status_code == 403
    assert renderizador.chamadas == []


def test_emissor_registrado_em_teste_emite_por_tipo(api, cenario, emissor_teste):
    client, storage, renderizador, tipos_pedidos = api
    teste_id = cenario["teste_id"]
    headers = _auth(cenario["usuarios"]["auditor"])

    primeira = client.post(_url(teste_id, "teste"), headers=headers)
    segunda = client.post(_url(teste_id, "TESTE"), headers=headers)

    assert primeira.status_code == 201, primeira.text
    assert (primeira.json()["tipo"], primeira.json()["versao"]) == ("TESTE", "V01")
    assert segunda.json()["versao"] == "V02"
    assert tipos_pedidos == ["TESTE", "TESTE"]
    for versao in ("v01", "v02"):
        assert storage.objetos[f"relatorios/{teste_id}/teste-{versao}.pdf"] == b"%PDF-1.7 fake"
        assert storage.objetos[f"relatorios/{teste_id}/teste-{versao}.docx"] == b"PK fake docx"
    _formato, contexto, fotos = renderizador.chamadas[0]
    assert contexto["inspecao"]["tipo"] == "TESTE"
    assert fotos == {FOTO_TESTE: b"\xff\xd8 teste"}


def test_emissor_com_contexto_incompleto_retorna_422_generico(api, cenario, emissor_teste):
    client, _, renderizador, _ = api
    registrar_emissor(
        "TESTE",
        Emissor(
            tipo="TESTE",
            montar_contexto=_contexto_teste,
            validar_contexto=lambda ctx: ["titulo"],
            extrair_fotos=lambda ctx: set(),
            pipeline="pipeline_que_nao_existe",
        ),
    )
    response = client.post(_url(cenario["teste_id"], "TESTE"), headers=_auth(cenario["usuarios"]["auditor"]))
    assert response.status_code == 422
    assert response.json()["type"].endswith("/teste-contexto-incompleto")
    assert renderizador.chamadas == []


def _emitir_rfo(client, cenario) -> dict:
    response = client.post(_url(cenario["rfo_id"], "rfo"), headers=_auth(cenario["usuarios"]["auditor"]))
    assert response.status_code == 201, response.text
    return response.json()


def test_listagem_de_versoes(api, cenario):
    client, _, _, _ = api
    v1 = _emitir_rfo(client, cenario)
    v2 = _emitir_rfo(client, cenario)

    response = client.get(
        f"/api/v1/inspecoes/{cenario['rfo_id']}/relatorios", headers=_auth(cenario["usuarios"]["auxiliar"])
    )

    assert response.status_code == 200
    itens = response.json()
    assert [i["id"] for i in itens] == [v2["id"], v1["id"]]
    assert {k for k in itens[0]} == {"id", "tipo", "versao", "status", "emitido_em", "tem_pdf", "tem_docx"}
    assert [(i["tipo"], i["versao"], i["status"]) for i in itens] == [("RFO", "V02", "emitido"), ("RFO", "V01", "emitido")]
    assert all(i["tem_pdf"] and i["tem_docx"] and i["emitido_em"] for i in itens)


def test_listagem_de_inspecao_sem_relatorio_e_inexistente(api, cenario):
    client, _, _, _ = api
    headers = _auth(cenario["usuarios"]["auditor"])
    assert client.get(f"/api/v1/inspecoes/{cenario['ltip_id']}/relatorios", headers=headers).json() == []
    assert client.get(f"/api/v1/inspecoes/{uuid.uuid4()}/relatorios", headers=headers).status_code == 404
    cliente = client.get(
        f"/api/v1/inspecoes/{cenario['rfo_id']}/relatorios", headers=_auth(cenario["usuarios"]["cliente"])
    )
    assert cliente.status_code == 403


@pytest.mark.parametrize(("role", "esperado"), [("auditor", 200), ("auxiliar", 200), ("cliente", 403)])
def test_download_por_papel(api, cenario, role, esperado):
    client, _, _, _ = api
    emitido = _emitir_rfo(client, cenario)

    response = client.get(
        f"/api/v1/inspecoes/{cenario['rfo_id']}/relatorios/{emitido['id']}/download/PDF",
        headers=_auth(cenario["usuarios"][role]),
    )

    assert response.status_code == esperado, response.text
    if esperado == 200:
        body = response.json()
        assert body["relatorio_id"] == emitido["id"]
        assert body["formato"] == "pdf"
        assert f"relatorios/{cenario['rfo_id']}/rfo-v01.pdf" in body["url"]
        assert body["expira_em_segundos"] > 0
    else:
        assert response.json()["type"].endswith("/acesso-negado")


def test_download_docx_e_formato_invalido(api, cenario):
    client, _, _, _ = api
    emitido = _emitir_rfo(client, cenario)
    headers = _auth(cenario["usuarios"]["auditor"])
    base = f"/api/v1/inspecoes/{cenario['rfo_id']}/relatorios/{emitido['id']}/download"

    docx = client.get(f"{base}/docx", headers=headers)
    assert docx.status_code == 200
    assert docx.json()["url"].split("?")[0].endswith("rfo-v01.docx")
    invalido = client.get(f"{base}/xlsx", headers=headers)
    assert invalido.status_code == 404
    assert invalido.json()["type"].endswith("/formato-nao-suportado")


def test_download_de_relatorio_de_outra_inspecao_retorna_404(api, cenario):
    client, _, _, _ = api
    emitido = _emitir_rfo(client, cenario)

    response = client.get(
        f"/api/v1/inspecoes/{cenario['ltip_id']}/relatorios/{emitido['id']}/download/pdf",
        headers=_auth(cenario["usuarios"]["auditor"]),
    )

    assert response.status_code == 404
    assert response.json()["type"].endswith("/relatorio-nao-encontrado")


async def test_servico_emite_com_renderizador_do_emissor_quando_nao_injetado(cenario, emissor_teste, monkeypatch):
    """Sem renderizador injetado, `emitir_relatorio` usa `Emissor.criar_renderizador()`."""
    fake = FakeRenderizador()
    monkeypatch.setattr(Emissor, "criar_renderizador", lambda self: fake)
    storage = FakeStorage({FOTO_TESTE: b"x"})

    async with _TestSessionLocal() as s:
        relatorio = await relatorio_service.emitir_relatorio(s, cenario["teste_id"], "teste", storage)
    assert (relatorio.tipo, relatorio.versao) == ("TESTE", "V01")
    assert [c[0] for c in fake.chamadas] == ["pdf", "docx"]
