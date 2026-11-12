"""Testes da montagem do contexto do LTIP e do RFIP a partir do banco (V1-03).

`montar_contexto_ltip`/`montar_contexto_rfip`, validadores, emissores registrados e
`POST /inspecoes/{id}/relatorios/{LTIP|RFIP}` com storage e renderizador fakes (sem MinIO nem
WeasyPrint). Os testes com banco exigem o PostgreSQL de 05_infra/docker-compose.yml (localhost:5433).
"""
import io
import uuid
from datetime import date

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.v1.relatorios import get_renderizador_por_tipo
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import (
    Contrato,
    ContratoNbr,
    Edificacao,
    Foto,
    Inspecao,
    Ocorrencia,
    Relatorio,
    Responsavel,
    SistemaPredial,
    Subsistema,
    Usuario,
)
from app.models.tipo_servico import TipoServico
from app.schemas.relatorio_conteudo import ConteudoDados
from app.services import relatorio_conteudo_service
from app.services.relatorio_service import obter_emissor
from app.services.report_generator import ltip_pipeline, rfip_pipeline
from app.services.report_generator.ltip_contexto import (
    montar_contexto_ltip,
    validar_contexto_ltip,
)
from app.services.report_generator.rfip_contexto import (
    montar_contexto_rfip,
    validar_contexto_rfip,
)
from app.services.storage import get_storage_client
from tests.test_relatorios_rfo_api import FakeRenderizador, FakeStorage

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)

SUGESTAO_IA = "SUGESTAO-IA-NAO-APROVADA"


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


def _auth(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario.id))}"}


def _jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 24), (120, 80, 40)).save(buffer, format="JPEG")
    return buffer.getvalue()


async def _criar_cenario(tipo: str, *, com_crea: bool = True, com_art: bool = True):
    """Inspeção do `tipo` com 2 sistemas (fora de ordem), 3 ocorrências e 3 fotos (uma com IA em rascunho)."""
    sufixo = uuid.uuid4().hex[:8]
    chaves = {n: f"fotos/v103-{sufixo}-{n}.jpg" for n in ("manual", "ia", "segunda")}
    async with _TestSessionLocal() as s:
        auditor = Usuario(
            nome="Auditor V1-03",
            email=f"auditor-v103-{sufixo}@garra.com",
            senha_hash=hash_password("senha-forte-123"),
            ativo=True,
            role="auditor",
        )
        fiscal = Responsavel(
            nome="Eng. Fiscal V1-03",
            tipo="fiscal",
            crea="1234567/D-GO" if com_crea else None,
            email="fiscal@example.com",
            telefone="(62) 90000-0000",
            titulo_profissional="Engenheiro Civil",
        )
        edificacao = Edificacao(
            nome=f"Condomínio V1-03 {sufixo}",
            endereco="Rua Teste, 10, Setor Sul, Goiânia-GO",
            documentos_tecnicos={"itens": [{"nome": "projeto-estrutural.pdf", "tipo": "projeto", "storage_key": "x"}]},
        )
        # `ordem` invertida em relação a `seq_numero`: Hidráulica é a 1ª ocorrência, mas Estrutura sai antes.
        estrutura = SistemaPredial(nome=f"Estrutura V1-03 {sufixo}", ordem=901)
        hidraulica = SistemaPredial(nome=f"Hidráulica V1-03 {sufixo}", ordem=902)
        s.add_all([auditor, fiscal, edificacao, estrutura, hidraulica])
        await s.commit()
        vigas = Subsistema(sistema_id=estrutura.id, nome="Vigas", ordem=1)
        s.add(vigas)
        contrato = Contrato(
            edificacao_id=edificacao.id,
            fiscal_id=fiscal.id,
            numero=f"CT-V103-{sufixo}",
            tipo_servico=tipo,
            status="em_andamento",
            objeto="Inspeção predial do condomínio",
            art_fiscalizacao="ART-123" if com_art else None,
        )
        s.add(contrato)
        await s.commit()
        s.add(ContratoNbr(contrato_id=contrato.id, codigo_nbr="NBR 16747", descricao="Inspeção predial"))
        inspecao = Inspecao(contrato_id=contrato.id, tipo=tipo, status="em_andamento")
        s.add(inspecao)
        await s.commit()

        oc_hid = Ocorrencia(
            inspecao_id=inspecao.id, sistema_id=hidraulica.id, situacao="Não Conforme", classificacao="Anomalia",
            seq_numero=1, localizacao="Garagem", descricao="Vazamento no ralo.", grau_risco="MEDIO", prioridade=3,
            gut_gravidade=3.0, gut_urgencia=2.0, gut_tendencia=2.0,
        )  # fmt: skip
        oc_viga = Ocorrencia(
            inspecao_id=inspecao.id, sistema_id=estrutura.id, subsistema_id=vigas.id, situacao="Não Conforme",
            classificacao="Falha", seq_numero=2, localizacao="Subsolo", descricao="Armadura exposta.",
            grau_risco="CRITICO", prioridade=5, gut_gravidade=5.0, gut_urgencia=5.0, gut_tendencia=4.0,
        )  # fmt: skip
        oc_sem = Ocorrencia(
            inspecao_id=inspecao.id, sistema_id=estrutura.id, situacao="Conforme", classificacao="Conforme",
            seq_numero=3,
        )  # fmt: skip
        s.add_all([oc_hid, oc_viga, oc_sem])
        await s.commit()
        s.add_all(
            [
                Foto(ocorrencia_id=oc_hid.id, storage_key=chaves["manual"], origem="upload",
                     legenda="Ralo com infiltração.", ordem=1),
                Foto(ocorrencia_id=oc_viga.id, storage_key=chaves["ia"], origem="upload", ordem=1,
                     legenda_ia_sugerida=SUGESTAO_IA, status_validacao_ia="rascunho"),
                Foto(ocorrencia_id=oc_viga.id, storage_key=chaves["segunda"], origem="upload",
                     legenda="Segunda foto.", ordem=2),
            ]
        )  # fmt: skip
        await s.commit()
        cenario = {
            "auditor": auditor,
            "inspecao_id": inspecao.id,
            "chaves": chaves,
            "sistemas": {"estrutura": estrutura, "hidraulica": hidraulica},
            "edificacao": edificacao,
            "ids": {
                "contrato": contrato.id,
                "fiscal": fiscal.id,
                "edificacao": edificacao.id,
                "sistemas": [estrutura.id, hidraulica.id],
                "ocorrencias": [oc_hid.id, oc_viga.id, oc_sem.id],
                "subsistema": vigas.id,
            },
        }
    return cenario


async def _limpar(cenario) -> None:
    ids = cenario["ids"]
    async with _TestSessionLocal() as s:
        await s.execute(delete(Relatorio).where(Relatorio.inspecao_id == cenario["inspecao_id"]))
        await s.execute(delete(Foto).where(Foto.ocorrencia_id.in_(ids["ocorrencias"])))
        await s.execute(delete(Ocorrencia).where(Ocorrencia.id.in_(ids["ocorrencias"])))
        await s.execute(delete(Inspecao).where(Inspecao.id == cenario["inspecao_id"]))  # cascata: conteúdo
        await s.execute(delete(ContratoNbr).where(ContratoNbr.contrato_id == ids["contrato"]))
        await s.execute(delete(Contrato).where(Contrato.id == ids["contrato"]))
        await s.execute(delete(Edificacao).where(Edificacao.id == ids["edificacao"]))
        await s.execute(delete(Subsistema).where(Subsistema.id == ids["subsistema"]))
        await s.execute(delete(SistemaPredial).where(SistemaPredial.id.in_(ids["sistemas"])))
        await s.execute(delete(Responsavel).where(Responsavel.id == ids["fiscal"]))
        await s.execute(delete(Usuario).where(Usuario.id == cenario["auditor"].id))
        await s.commit()


@pytest_asyncio.fixture
async def cenario_ltip():
    cenario = await _criar_cenario("LTIP")
    yield cenario
    await _limpar(cenario)


@pytest_asyncio.fixture
async def cenario_rfip():
    cenario = await _criar_cenario("RFIP")
    yield cenario
    await _limpar(cenario)


@pytest_asyncio.fixture
async def cenario_ltip_sem_fiscal_crea():
    cenario = await _criar_cenario("LTIP", com_crea=False)
    yield cenario
    await _limpar(cenario)


@pytest.fixture
def api():
    storage = FakeStorage()
    renderizador = FakeRenderizador()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_storage_client] = lambda: storage
    app.dependency_overrides[get_renderizador_por_tipo] = lambda: (lambda tipo: renderizador)
    yield TestClient(app), storage, renderizador
    for dep in (get_db, get_storage_client, get_renderizador_por_tipo):
        app.dependency_overrides.pop(dep, None)


async def _montar(montar, cenario) -> dict:
    async with _TestSessionLocal() as s:
        return await montar(s, cenario["inspecao_id"])


def _fotos_de(contexto) -> set[str]:
    return {f["storage_key"] for o in contexto["ocorrencias"] for f in o["fotos"]}


# --- unidade (sem banco) -------------------------------------------------------


@pytest.mark.parametrize(("tipo", "pipeline"), [("ltip", "ltip_pipeline"), ("RFIP", "rfip_pipeline")])
def test_emissores_registrados(tipo, pipeline):
    emissor = obter_emissor(tipo)
    assert emissor.tipo == tipo.upper()
    assert emissor.pipeline == pipeline


def test_extrair_fotos_so_a_primeira_de_cada_ocorrencia():
    contexto = {
        "ocorrencias": [
            {"fotos": [{"storage_key": "a"}, {"storage_key": "b"}]},
            {"fotos": []},
            {"fotos": [{"storage_key": "c"}]},
        ]
    }
    assert obter_emissor("LTIP").extrair_fotos(contexto) == {"a", "c"}
    assert obter_emissor("RFIP").extrair_fotos(contexto) == {"a", "c"}
    assert obter_emissor("RFIP").extrair_fotos({}) == set()


def test_validar_ltip_lista_campos_faltantes():
    completo = {
        "edificacao": {"nome": "E"},
        "fiscal": {"nome": "N", "crea": "1"},
        "contrato": {"art_fiscalizacao": "ART"},
    }
    assert validar_contexto_ltip(completo) == []
    assert validar_contexto_ltip({}) == [
        "edificacao.nome", "fiscal.nome", "fiscal.crea", "contrato.art_fiscalizacao"
    ]  # fmt: skip
    # '—' (DEC-33) conta como ausente
    completo["fiscal"]["crea"] = "—"
    completo["contrato"]["art_fiscalizacao"] = "  "
    assert validar_contexto_ltip(completo) == ["fiscal.crea", "contrato.art_fiscalizacao"]


def test_validar_rfip_lista_campos_faltantes():
    assert validar_contexto_rfip({"responsavel": {"nome": "N", "crea": "1"}}) == []
    assert validar_contexto_rfip({"responsavel": {"nome": "N", "crea": None}}) == ["responsavel.crea"]
    assert validar_contexto_rfip({}) == ["responsavel.nome", "responsavel.crea"]


# --- com banco -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ltip_do_banco_passa_no_normalizar_contexto(cenario_ltip):
    cenario = cenario_ltip
    contexto = await _montar(montar_contexto_ltip, cenario)

    assert validar_contexto_ltip(contexto) == []
    assert contexto["edificacao"]["nome"] == cenario["edificacao"].nome
    assert contexto["fiscal"] == {
        "nome": "Eng. Fiscal V1-03", "titulo_profissional": "Engenheiro Civil", "crea": "1234567/D-GO",
        "email": "fiscal@example.com", "telefone": "(62) 90000-0000",
    }  # fmt: skip
    assert contexto["contrato"]["art_fiscalizacao"] == "ART-123"
    assert contexto["data_emissao"] == date.today().strftime("%d/%m/%Y")
    assert contexto["objeto_paragrafos"] == ["Inspeção predial do condomínio"]
    documentacao = contexto["documentacao_analisada_paragrafos"]
    assert "Normas técnicas consideradas: NBR 16747 (Inspeção predial)." in documentacao
    assert "Documentos técnicos da edificação analisados: projeto-estrutural.pdf (projeto)." in documentacao
    assert contexto["introducao_paragrafos"]  # padrão do tipo

    normalizado = ltip_pipeline.normalizar_contexto(contexto)
    assert [s["nome"] for s in normalizado["sistemas"]] == [
        cenario["sistemas"]["estrutura"].nome,
        cenario["sistemas"]["hidraulica"].nome,
    ]
    estrutura = normalizado["sistemas"][0]["ocorrencias"]
    assert [o["seq_numero"] for o in estrutura] == [2, 3]  # subsistema "Vigas" (ordem 1) antes do sem subsistema
    viga = estrutura[0]
    assert (viga["gut_gravidade"], viga["gut_urgencia"], viga["gut_tendencia"], viga["pontuacao_gut"]) == (5, 5, 4, 100)
    assert (viga["grau_risco"], viga["prioridade"], viga["subsistema"], viga["localizacao"]) == ("CRITICO", 5, "Vigas", "Subsolo")
    sem_dados = estrutura[1]
    assert (sem_dados["localizacao"], sem_dados["descricao"], sem_dados["subsistema"], sem_dados["grau_risco"]) == ("—",) * 4
    html = ltip_pipeline.renderizar_html(contexto, {k: _jpeg() for k in _fotos_de(contexto)})
    assert "None" not in html
    assert "{{" not in html
    assert "Inspeção predial do condomínio" in html


@pytest.mark.asyncio
async def test_ltip_texto_salvo_vence_os_padroes_montados(cenario_ltip):
    cenario = cenario_ltip
    async with _TestSessionLocal() as s:
        await relatorio_conteudo_service.salvar(
            s,
            cenario["inspecao_id"],
            TipoServico.LTIP,
            ConteudoDados(
                data_emissao=date(2026, 3, 4),
                local_emissao="Goiânia-GO",
                textos={"objeto": ["Objeto do auditor."], "documentacao_analisada": ["Só o que o auditor listou."]},
            ),
            usuario_id=None,
        )
    contexto = await _montar(montar_contexto_ltip, cenario)
    assert contexto["objeto_paragrafos"] == ["Objeto do auditor."]
    assert contexto["documentacao_analisada_paragrafos"] == ["Só o que o auditor listou."]
    assert contexto["data_emissao"] == "04/03/2026"
    assert contexto["local_emissao"] == "Goiânia-GO"
    assert ltip_pipeline.normalizar_contexto(contexto)["data_emissao"] == "04/03/2026"


@pytest.mark.asyncio
async def test_legenda_nao_aprovada_nao_aparece(cenario_ltip, cenario_rfip):
    for montar, cenario, pipeline in (
        (montar_contexto_ltip, cenario_ltip, ltip_pipeline),
        (montar_contexto_rfip, cenario_rfip, rfip_pipeline),
    ):
        contexto = await _montar(montar, cenario)
        assert SUGESTAO_IA not in repr(contexto)
        viga = next(o for o in contexto["ocorrencias"] if o["seq_numero"] == 2)
        assert [f["legenda"] for f in viga["fotos"]] == ["—", "Segunda foto."]
        assert viga["fotos"][0]["storage_key"] == cenario["chaves"]["ia"]
        assert SUGESTAO_IA not in repr(pipeline.normalizar_contexto(contexto))
        manual = next(o for o in contexto["ocorrencias"] if o["seq_numero"] == 1)
        assert manual["fotos"][0]["legenda"] == "Ralo com infiltração."


@pytest.mark.asyncio
async def test_rfip_do_banco_passa_no_normalizar_contexto(cenario_rfip):
    cenario = cenario_rfip
    contexto = await _montar(montar_contexto_rfip, cenario)

    assert validar_contexto_rfip(contexto) == []
    assert contexto["responsavel"]["nome"] == "Eng. Fiscal V1-03"
    assert contexto["responsavel"]["titulo_profissional"] == "Engenheiro Civil"
    assert contexto["incluir_resumo"] is True  # padrão

    normalizado = rfip_pipeline.normalizar_contexto(contexto)
    assert [s["nome"] for s in normalizado["sistemas"]] == [
        cenario["sistemas"]["estrutura"].nome,
        cenario["sistemas"]["hidraulica"].nome,
    ]
    assert normalizado["incluir_resumo"] is True
    html = rfip_pipeline.renderizar_html(contexto, {k: _jpeg() for k in _fotos_de(contexto)})
    assert "None" not in html
    assert "Eng. Fiscal V1-03" in html


@pytest.mark.asyncio
async def test_rfip_incluir_resumo_do_conteudo(cenario_rfip):
    async with _TestSessionLocal() as s:
        await relatorio_conteudo_service.salvar(
            s, cenario_rfip["inspecao_id"], TipoServico.RFIP, ConteudoDados(incluir_resumo=False), usuario_id=None
        )
    contexto = await _montar(montar_contexto_rfip, cenario_rfip)
    assert contexto["incluir_resumo"] is False


@pytest.mark.asyncio
async def test_ordem_por_sistema_e_numero(cenario_ltip):
    contexto = await _montar(montar_contexto_ltip, cenario_ltip)
    assert [o["seq_numero"] for o in contexto["ocorrencias"]] == [1, 2, 3]
    ordens = {o["seq_numero"]: o["sistema_ordem"] for o in contexto["ocorrencias"]}
    assert ordens == {1: 902, 2: 901, 3: 901}  # a ordem do gabarito, não a do nº, define o agrupamento
    assert {o["seq_numero"]: o["subsistema_ordem"] for o in contexto["ocorrencias"]} == {1: None, 2: 1, 3: None}


@pytest.mark.asyncio
async def test_tipo_divergente_gera_409(cenario_rfip):
    from app.core.errors import ConflictError

    with pytest.raises(ConflictError) as erro:
        await _montar(montar_contexto_ltip, cenario_rfip)
    assert erro.value.type_suffix == "inspecao-nao-ltip"


def test_post_ltip_sem_crea_do_fiscal_retorna_422(api, cenario_ltip_sem_fiscal_crea):
    client, storage, renderizador = api
    cenario = cenario_ltip_sem_fiscal_crea
    response = client.post(
        f"/api/v1/inspecoes/{cenario['inspecao_id']}/relatorios/LTIP", headers=_auth(cenario["auditor"])
    )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["type"].endswith("/ltip-contexto-incompleto")
    assert [e["field"] for e in body["errors"]] == ["fiscal.crea"]
    assert renderizador.chamadas == []
    assert storage.objetos == {}


def test_post_rfip_sem_fiscal_crea_retorna_422(api, cenario_ltip_sem_fiscal_crea):
    # mesma inspeção reaproveitada como RFIP: troca o tipo no banco para exercitar o 422 do RFIP
    import asyncio

    cenario = cenario_ltip_sem_fiscal_crea
    client, _storage, renderizador = api

    async def _como_rfip():
        async with _TestSessionLocal() as s:
            inspecao = await s.get(Inspecao, cenario["inspecao_id"])
            inspecao.tipo = "RFIP"
            await s.commit()

    asyncio.run(_como_rfip())
    response = client.post(
        f"/api/v1/inspecoes/{cenario['inspecao_id']}/relatorios/RFIP", headers=_auth(cenario["auditor"])
    )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["type"].endswith("/rfip-contexto-incompleto")
    assert [e["field"] for e in body["errors"]] == ["responsavel.crea"]
    assert renderizador.chamadas == []


@pytest.mark.parametrize("tipo", ["LTIP", "RFIP"])
def test_post_cria_versao_1_com_renderizador_fake(api, request, tipo):
    cenario = request.getfixturevalue(f"cenario_{tipo.lower()}")
    client, storage, renderizador = api
    for chave in cenario["chaves"].values():
        storage.objetos[chave] = _jpeg()
    inspecao_id = cenario["inspecao_id"]

    response = client.post(f"/api/v1/inspecoes/{inspecao_id}/relatorios/{tipo}", headers=_auth(cenario["auditor"]))

    assert response.status_code == 201, response.text
    corpo = response.json()
    assert (corpo["tipo"], corpo["versao"], corpo["tem_pdf"], corpo["tem_docx"]) == (tipo, "V01", True, True)
    assert storage.objetos[f"relatorios/{inspecao_id}/{tipo.lower()}-v01.pdf"] == b"%PDF-1.7 fake"
    assert storage.objetos[f"relatorios/{inspecao_id}/{tipo.lower()}-v01.docx"] == b"PK fake docx"
    assert [c[0] for c in renderizador.chamadas] == ["pdf", "docx"]
    # só a 1ª foto de cada ocorrência é baixada: a 2ª foto da viga ("segunda") fica de fora
    _formato, _contexto, fotos = renderizador.chamadas[0]
    assert set(fotos) == {cenario["chaves"]["manual"], cenario["chaves"]["ia"]}
