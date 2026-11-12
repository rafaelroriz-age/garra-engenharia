"""Testes da montagem do contexto da Vistoria Cautelar a partir do banco (V1-04).

`montar_contexto_vistoria_cautelar`, `validar_contexto_vistoria_cautelar`, o
emissor registrado e `POST /inspecoes/{id}/relatorios/VISTORIA_CAUTELAR` com
storage e renderizador fakes (sem MinIO nem WeasyPrint). Os testes com banco
exigem o PostgreSQL de 05_infra/docker-compose.yml (localhost:5433).
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
    Edificacao,
    Foto,
    Inspecao,
    Ocorrencia,
    Relatorio,
    Responsavel,
    SistemaPredial,
    Usuario,
)
from app.models.tipo_servico import TipoServico
from app.schemas.relatorio_conteudo import ConteudoDados
from app.services import relatorio_conteudo_service
from app.services.relatorio_service import obter_emissor
from app.services.report_generator import vistoria_cautelar_pipeline as pipeline
from app.services.report_generator.vistoria_cautelar_contexto import (
    TIPO_VISTORIA_CAUTELAR,
    cidade_do_endereco,
    extrair_fotos_vistoria_cautelar,
    montar_contexto_vistoria_cautelar,
    validar_contexto_vistoria_cautelar,
)
from app.services.storage import get_storage_client
from tests.test_relatorios_rfo_api import FakeRenderizador, FakeStorage

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)

SUGESTAO_IA = "SUGESTAO-IA-NAO-APROVADA"
PARECER = "Recebimento provisório com ressalvas"
METODOLOGIA = "Remover o revestimento solto e reassentar com argamassa colante AC-III."
FUNDAMENTACAO = "NBR 13755: revestimento cerâmico de fachada."


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


def _auth(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario.id))}"}


def _jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 24), (120, 80, 40)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest_asyncio.fixture
async def cenario():
    """Inspeção VISTORIA_CAUTELAR com 2 sistemas, 3 ocorrências e 3 fotos (uma com IA em rascunho)."""
    sufixo = uuid.uuid4().hex[:8]
    chaves = {
        "manual": f"fotos/v104-{sufixo}-manual.jpg",
        "ia": f"fotos/v104-{sufixo}-ia.jpg",
        "segunda": f"fotos/v104-{sufixo}-segunda.jpg",
        "assinatura": f"assinaturas/v104-{sufixo}.png",
    }
    async with _TestSessionLocal() as s:
        auditor = Usuario(
            nome="Auditor V1-04",
            email=f"auditor-v104-{sufixo}@garra.com",
            senha_hash=hash_password("senha-forte-123"),
            ativo=True,
            role="auditor",
        )
        fiscal = Responsavel(
            nome="Eng. Fiscal V1-04",
            tipo="fiscal",
            crea="1234567/D-GO",
            email="fiscal@example.com",
            telefone="(62) 90000-0000",
            titulo_profissional="Engenheiro Civil",
            qualificacoes=["Especialista em Patologia das Construções"],
            assinatura_storage_key=chaves["assinatura"],
        )
        edificacao = Edificacao(
            nome=f"Condomínio V1-04 {sufixo}",
            endereco="Rua Teste, 10, Setor Sul, Goiânia-GO, 74000-000",
            cep="74000-000",
            tipologia="Residencial multifamiliar",
            sistema_construtivo="Concreto armado",
            descricao_pavimentos="Térreo + 12 pavimentos",
            area_total_m2=1234.5,
        )
        revestimentos = SistemaPredial(nome=f"Revestimentos V1-04 {sufixo}", ordem=901)
        hidraulica = SistemaPredial(nome=f"Hidráulica V1-04 {sufixo}", ordem=902)
        s.add_all([auditor, fiscal, edificacao, revestimentos, hidraulica])
        await s.commit()

        contrato = Contrato(
            edificacao_id=edificacao.id,
            fiscal_id=fiscal.id,
            numero=f"CT-V104-{sufixo}",
            tipo_servico=TIPO_VISTORIA_CAUTELAR,
            status="em_andamento",
            objeto="Reforma da fachada e áreas comuns",
        )
        s.add(contrato)
        await s.commit()
        inspecao = Inspecao(contrato_id=contrato.id, tipo=TIPO_VISTORIA_CAUTELAR, status="em_andamento")
        s.add(inspecao)
        await s.commit()

        # seq 2 é de Revestimentos (ordem 901) e seq 1 de Hidráulica: sistemas saem por `ordem`.
        oc_hidraulica = Ocorrencia(
            inspecao_id=inspecao.id, sistema_id=hidraulica.id, situacao="Não Conforme",
            classificacao="Anomalia", seq_numero=1, localizacao="Garagem", descricao="Vazamento no ralo.",
        )  # fmt: skip
        oc_fachada = Ocorrencia(
            inspecao_id=inspecao.id, sistema_id=revestimentos.id, situacao="Não Conforme",
            classificacao="Anomalia", seq_numero=2, localizacao="Fachada norte", descricao="Placas cerâmicas soltas.",
        )  # fmt: skip
        oc_hall = Ocorrencia(
            inspecao_id=inspecao.id, sistema_id=revestimentos.id, situacao="Não Conforme",
            classificacao="Anomalia", seq_numero=3, localizacao="Hall", descricao="Fissura no reboco.",
        )  # fmt: skip
        s.add_all([oc_hidraulica, oc_fachada, oc_hall])
        await s.commit()

        s.add_all(
            [
                Foto(ocorrencia_id=oc_hidraulica.id, storage_key=chaves["manual"], origem="upload",
                     legenda="Ralo com infiltração.", ordem=1),
                Foto(ocorrencia_id=oc_fachada.id, storage_key=chaves["ia"], origem="upload", ordem=1,
                     legenda_ia_sugerida=SUGESTAO_IA, status_validacao_ia="rascunho"),
                Foto(ocorrencia_id=oc_fachada.id, storage_key=chaves["segunda"], origem="upload",
                     legenda="Detalhe das placas.", ordem=2),
            ]
        )  # fmt: skip
        await s.commit()

        yield {
            "auditor": auditor,
            "inspecao_id": inspecao.id,
            "chaves": chaves,
            "ocorrencias": {"hidraulica": oc_hidraulica.id, "fachada": oc_fachada.id, "hall": oc_hall.id},
            "sistemas": {"revestimentos": revestimentos, "hidraulica": hidraulica},
            "edificacao": edificacao,
            "fiscal_id": fiscal.id,
        }

        ocorrencias = [oc_hidraulica.id, oc_fachada.id, oc_hall.id]
        await s.execute(delete(Relatorio).where(Relatorio.inspecao_id == inspecao.id))
        await s.execute(delete(Foto).where(Foto.ocorrencia_id.in_(ocorrencias)))
        await s.execute(delete(Ocorrencia).where(Ocorrencia.id.in_(ocorrencias)))
        await s.execute(delete(Inspecao).where(Inspecao.id == inspecao.id))  # cascata: relatorio_conteudos
        await s.execute(delete(Contrato).where(Contrato.id == contrato.id))
        await s.execute(delete(Edificacao).where(Edificacao.id == edificacao.id))
        await s.execute(delete(SistemaPredial).where(SistemaPredial.id.in_([revestimentos.id, hidraulica.id])))
        await s.execute(delete(Responsavel).where(Responsavel.id == fiscal.id))
        await s.execute(delete(Usuario).where(Usuario.id == auditor.id))
        await s.commit()


def _dados_conteudo(cenario, *, parecer: str | None = PARECER) -> dict:
    dados = {
        "datas_vistorias": ["2026-10-05", "2026-10-19"],
        "metodologia_corretiva": {str(cenario["ocorrencias"]["fachada"]): METODOLOGIA},
        "fundamentacao_tecnica": {str(cenario["sistemas"]["revestimentos"].id): [FUNDAMENTACAO]},
        "textos": {"introducao": ["Introdução específica desta obra."]},
    }
    if parecer is not None:
        dados["parecer"] = parecer
    return dados


async def _salvar_conteudo(cenario, *, parecer: str | None = PARECER) -> None:
    async with _TestSessionLocal() as s:
        await relatorio_conteudo_service.salvar(
            s,
            cenario["inspecao_id"],
            TipoServico.VISTORIA_CAUTELAR,
            ConteudoDados(**_dados_conteudo(cenario, parecer=parecer)),
            usuario_id=None,
        )


async def _montar(cenario) -> dict:
    async with _TestSessionLocal() as s:
        return await montar_contexto_vistoria_cautelar(s, cenario["inspecao_id"])


@pytest.fixture
def api():
    storage = FakeStorage()
    renderizador = FakeRenderizador()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_storage_client] = lambda: storage
    app.dependency_overrides[get_renderizador_por_tipo] = lambda: (lambda tipo: renderizador)
    yield TestClient(app), storage, renderizador
    for dep in (get_storage_client, get_renderizador_por_tipo):
        app.dependency_overrides.pop(dep, None)


# --- unidade (sem banco) -------------------------------------------------------


def test_emissor_registrado():
    emissor = obter_emissor("vistoria_cautelar")
    assert emissor.tipo == TIPO_VISTORIA_CAUTELAR
    assert emissor.montar_contexto is montar_contexto_vistoria_cautelar
    assert emissor.validar_contexto is validar_contexto_vistoria_cautelar
    assert emissor.extrair_fotos is extrair_fotos_vistoria_cautelar
    assert emissor.pipeline == "vistoria_cautelar_pipeline"


def test_extrair_fotos_inclui_figuras_assinatura_e_capa():
    contexto = {
        "figuras": [{"storage_key": "a"}, {"storage_key": None}, {"storage_key": "b"}],
        "assinatura_storage_key": "assinatura",
        "capa_fundo_storage_key": "capa",
    }
    assert extrair_fotos_vistoria_cautelar(contexto) == {"a", "b", "assinatura", "capa"}
    assert extrair_fotos_vistoria_cautelar({"figuras": []}) == set()


def test_validar_aponta_fiscal_e_parecer_por_campo():
    completo = {"responsavel": {"nome": "Eng.", "crea": "1"}, "complementos": {"parecer_tecnico": "Ok"}}
    assert validar_contexto_vistoria_cautelar(completo) == []
    sem = {"responsavel": {"nome": "Eng.", "crea": "  "}, "complementos": {"parecer_tecnico": None}}
    assert validar_contexto_vistoria_cautelar(sem) == ["responsavel.crea", "complementos.parecer_tecnico"]
    assert validar_contexto_vistoria_cautelar({}) == [
        "responsavel.nome",
        "responsavel.crea",
        "complementos.parecer_tecnico",
    ]


@pytest.mark.parametrize(
    ("endereco", "cidade"),
    [
        ("Rua A, 1, Setor Sul, Goiânia-GO, 74000-000", "Goiânia-GO"),
        ("Av. B, 200 - Centro, Aparecida de Goiânia / go", "Aparecida de Goiânia-GO"),
        ("Rua C, 3, Setor Oeste", None),
        (None, None),
    ],
)
def test_cidade_do_endereco(endereco, cidade):
    assert cidade_do_endereco(endereco) == cidade


# --- com banco -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_contexto_do_banco_passa_no_normalizar_contexto(cenario):
    await _salvar_conteudo(cenario)
    contexto = await _montar(cenario)

    assert validar_contexto_vistoria_cautelar(contexto) == []
    assert contexto["responsavel"]["nome"] == "Eng. Fiscal V1-04"
    assert contexto["responsavel"]["titulo_profissional"] == "Engenheiro Civil"
    assert contexto["obra"]["descricao"] == "Reforma da fachada e áreas comuns"
    assert contexto["edificacao"]["nome"] == cenario["edificacao"].nome
    assert contexto["data_emissao"] == date.today().isoformat()
    assert contexto["local_emissao"] == "Goiânia-GO"
    assert contexto["complementos"]["parecer_tecnico"] == PARECER
    assert contexto["assinatura_storage_key"] == cenario["chaves"]["assinatura"]
    assert contexto["conteudo"]["introducao"] == ["Introdução específica desta obra."]
    assert contexto["conteudo"]["encerramento"]  # padrão do tipo
    assert contexto["conteudo"]["datas_das_vistorias"] == ["As vistorias foram realizadas em 05/10/2026 e 19/10/2026."]
    identificacao = {linha["aspecto_tecnico"]: linha["descricao_detalhada"] for linha in contexto["tabelas"]["identificacao"]}
    assert identificacao["CEP"] == "74000-000"
    assert identificacao["Área total construída"] == "1.234,50 m²"

    assert [s["nome"] for s in contexto["sistemas"]] == [
        cenario["sistemas"]["revestimentos"].nome,
        cenario["sistemas"]["hidraulica"].nome,
    ]
    assert contexto["sistemas"][0]["constatacoes"] == ["Placas cerâmicas soltas.", "Fissura no reboco."]
    assert contexto["sistemas"][0]["fundamentacao_tecnica"] == [FUNDAMENTACAO]
    assert contexto["sistemas"][1]["fundamentacao_tecnica"] == []
    chaves = cenario["chaves"]
    assert [(f["numero"], f["storage_key"]) for f in contexto["figuras"]] == [
        (1, chaves["manual"]),
        (2, chaves["ia"]),
        (3, chaves["segunda"]),
    ]
    assert extrair_fotos_vistoria_cautelar(contexto) == {
        chaves["manual"], chaves["ia"], chaves["segunda"], chaves["assinatura"]
    }

    normalizado = pipeline.normalizar_contexto(contexto)
    assert normalizado["responsavel"]["qualificacoes"] == ["Especialista em Patologia das Construções"]
    assert normalizado["local_emissao"] == "Goiânia-GO"
    html = pipeline.renderizar_html(contexto, {k: _jpeg() for k in extrair_fotos_vistoria_cautelar(contexto)})
    assert "None" not in html
    assert "{{" not in html
    assert PARECER in html
    assert METODOLOGIA in html


@pytest.mark.asyncio
async def test_legenda_nao_aprovada_nao_entra(cenario):
    await _salvar_conteudo(cenario)
    contexto = await _montar(cenario)

    assert SUGESTAO_IA not in repr(contexto)
    figura_ia = contexto["figuras"][1]
    assert figura_ia["storage_key"] == cenario["chaves"]["ia"]
    assert figura_ia["legenda"] is None
    assert pipeline.normalizar_contexto(contexto)["figuras"][1]["legenda"] == "—"
    assert [f["legenda"] for f in contexto["figuras"]] == ["Ralo com infiltração.", None, "Detalhe das placas."]


@pytest.mark.asyncio
async def test_metodologia_corretiva_por_ocorrencia(cenario):
    await _salvar_conteudo(cenario)
    contexto = await _montar(cenario)

    assert contexto["tabelas"]["plano_de_correcoes_remanescentes"] == [
        {"item": "1", "localizacao": "Garagem", "descricao_da_pendencia": "Vazamento no ralo.",
         "metodologia_corretiva_indicada": "—"},
        {"item": "2", "localizacao": "Fachada norte", "descricao_da_pendencia": "Placas cerâmicas soltas.",
         "metodologia_corretiva_indicada": METODOLOGIA},
        {"item": "3", "localizacao": "Hall", "descricao_da_pendencia": "Fissura no reboco.",
         "metodologia_corretiva_indicada": "—"},
    ]  # fmt: skip


@pytest.mark.asyncio
async def test_sem_conteudo_salvo_usa_padroes_e_falta_parecer(cenario):
    contexto = await _montar(cenario)
    assert contexto["complementos"]["parecer_tecnico"] is None
    assert contexto["conteudo"]["datas_das_vistorias"] == []
    assert contexto["conteudo"]["referencias_bibliograficas"]  # padrão do tipo
    assert validar_contexto_vistoria_cautelar(contexto) == ["complementos.parecer_tecnico"]


def test_post_sem_parecer_retorna_422(api, cenario):
    client, storage, renderizador = api
    url = f"/api/v1/inspecoes/{cenario['inspecao_id']}/relatorios/VISTORIA_CAUTELAR"
    response = client.post(url, headers=_auth(cenario["auditor"]))

    assert response.status_code == 422, response.text
    body = response.json()
    assert body["type"].endswith("/vistoria_cautelar-contexto-incompleto")
    assert [e["field"] for e in body["errors"]] == ["complementos.parecer_tecnico"]
    assert renderizador.chamadas == []
    assert storage.objetos == {}


def test_post_cria_versao_1_com_renderizador_fake(api, cenario):
    client, storage, renderizador = api
    chaves = cenario["chaves"]
    for chave in chaves.values():
        storage.objetos[chave] = _jpeg()
    inspecao_id = cenario["inspecao_id"]
    salvo = client.put(
        f"/api/v1/inspecoes/{inspecao_id}/conteudo/VISTORIA_CAUTELAR",
        json={"dados": _dados_conteudo(cenario)},
        headers=_auth(cenario["auditor"]),
    )
    assert salvo.status_code == 200, salvo.text

    response = client.post(
        f"/api/v1/inspecoes/{inspecao_id}/relatorios/VISTORIA_CAUTELAR", headers=_auth(cenario["auditor"])
    )

    assert response.status_code == 201, response.text
    corpo = response.json()
    assert (corpo["tipo"], corpo["versao"], corpo["tem_pdf"], corpo["tem_docx"]) == (
        TIPO_VISTORIA_CAUTELAR, "V01", True, True
    )
    assert storage.objetos[f"relatorios/{inspecao_id}/vistoria_cautelar-v01.pdf"] == b"%PDF-1.7 fake"
    assert storage.objetos[f"relatorios/{inspecao_id}/vistoria_cautelar-v01.docx"] == b"PK fake docx"
    formatos = [chamada[0] for chamada in renderizador.chamadas]
    assert formatos == ["pdf", "docx"]
    _formato, contexto, fotos = renderizador.chamadas[0]
    assert contexto["complementos"]["parecer_tecnico"] == PARECER
    assert set(fotos) == set(chaves.values())
