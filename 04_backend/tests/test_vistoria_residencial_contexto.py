"""Testes da montagem do contexto da Vistoria Residencial a partir do banco (V1-05).

Unidade (sem banco): textos gerados da edificação/fiscal, cidade do endereço,
validação e imagens opcionais do storage. Integração (PostgreSQL de
05_infra/docker-compose.yml, localhost:5433): contexto montado com dados reais
passa no `normalizar_contexto` e renderiza o HTML sem 'None' nem '{{';
`POST .../relatorios/VISTORIA_RESIDENCIAL` com renderizador e storage fakes.
"""
import io
import re
import uuid
from datetime import date

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import delete, select
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
    RelatorioConteudo,
    Responsavel,
    SistemaPredial,
    Usuario,
)
from app.services.relatorio_service import obter_emissor
from app.services.report_generator import vistoria_residencial_contexto as ctx_mod
from app.services.report_generator import vistoria_residencial_pipeline as pipeline
from app.services.storage import get_storage_client
from tests.test_relatorios_rfo_api import FakeRenderizador, FakeStorage

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)

TIPO = "VISTORIA_RESIDENCIAL"
SUGESTAO_IA = "SUGESTAO-IA-NAO-APROVADA-V105"
TRAVESSAO = chr(0x2013)  # travessão curto, comum em endereços digitados


def _imagem(formato: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 24), (120, 60, 30)).save(buffer, format=formato)
    return buffer.getvalue()


def _auth(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario.id))}"}


# --- unidade (sem banco) -------------------------------------------------------------


def test_emissor_registrado():
    emissor = obter_emissor("vistoria_residencial")
    assert emissor.tipo == TIPO
    assert emissor.pipeline == "vistoria_residencial_pipeline"
    assert emissor.montar_contexto is ctx_mod.montar_contexto_vistoria_residencial
    assert emissor.validar_contexto is ctx_mod.validar_contexto_vistoria_residencial
    assert emissor.anexar_do_storage is ctx_mod.anexar_imagens_do_storage
    contexto = {"fotos": [{"storage_key": "a"}, {"storage_key": None}, {"storage_key": "b"}]}
    assert emissor.extrair_fotos(contexto) == {"a", "b"}


@pytest.mark.parametrize(
    ("endereco", "esperado"),
    [
        ("Rua 10, nº 200 - Setor Oeste, Goiânia - GO, 74000-000", "Goiânia-GO"),
        ("Av. Central, 5, Aparecida de Goiânia/GO", "Aparecida de Goiânia-GO"),
        (f"Rua X, 1 {TRAVESSAO} Anápolis {TRAVESSAO} GO", "Anápolis-GO"),
        ("Rua Genérica, 2", None),
        (None, None),
    ],
)
def test_cidade_do_endereco(endereco, esperado):
    assert ctx_mod.cidade_do_endereco(endereco) == esperado


def test_textos_gerados_da_edificacao_e_do_fiscal():
    edificacao = {
        "endereco": "Rua A, 1",
        "cep": "74000-000",
        "tipologia": "Residencial multifamiliar",
        "sistema_construtivo": "Concreto armado",
        "descricao_pavimentos": "Térreo e 20 pavimentos tipo.",
        "area_total_m2": 12345.5,
    }
    assert ctx_mod.texto_tipologia(edificacao) == ["Tipologia da edificação: Residencial multifamiliar."]
    assert ctx_mod.texto_caracterizacao(edificacao) == [
        "Sistema construtivo: Concreto armado.",
        "Pavimentos: Térreo e 20 pavimentos tipo.",
        "Área total construída: 12.345,50 m².",
    ]
    assert ctx_mod.texto_localizacao(edificacao) == ["Endereço: Rua A, 1.", "CEP: 74000-000."]
    assert ctx_mod.texto_caracterizacao({"area_total_m2": 80.0}) == ["Área total construída: 80 m²."]
    assert ctx_mod.texto_tipologia({}) == []
    assert ctx_mod.texto_responsavel({"nome": "Fulana", "crea": "1-GO", "email": "f@x.com"}) == [
        "A inspeção foi realizada pelo responsável técnico Fulana, CREA nº 1-GO.",
        "Contato: f@x.com.",
    ]
    assert ctx_mod.texto_datas_vistorias(["2026-11-05", "2026-11-04", "x"]) == [
        "As vistorias foram realizadas em 04/11/2026 e 05/11/2026."
    ]
    assert ctx_mod.texto_datas_vistorias(["2026-11-04"]) == ["A vistoria foi realizada em 04/11/2026."]
    assert ctx_mod.texto_datas_vistorias(None) == []


def test_validacao_por_campo():
    ok = {"fiscal": {"nome": "F", "crea": "1"}, "imovel": {"unidade": "Ap. 1"}}
    assert ctx_mod.validar_contexto_vistoria_residencial(ok) == []
    assert ctx_mod.validar_contexto_vistoria_residencial(
        {"fiscal": {"nome": "F", "crea": " "}, "imovel": {"unidade": "—"}}
    ) == ["fiscal.crea", "imovel.unidade"]
    assert ctx_mod.validar_contexto_vistoria_residencial({}) == ["fiscal.nome", "fiscal.crea", "imovel.unidade"]


def test_imagens_do_storage_opcionais_e_erro_vira_aviso():
    png = _imagem("PNG")
    storage = FakeStorage({"assinaturas/f.png": png, "docs/capa.txt": b"nao e imagem"})
    contexto = {"assinatura_storage_key": "assinaturas/f.png", "capa_fundo_storage_key": "docs/sumiu.jpg"}
    ctx_mod.anexar_imagens_do_storage(contexto, storage)
    assert contexto["assinatura_data_uri"].startswith("data:image/png;base64,")
    assert "capa_fundo_data_uri" not in contexto
    assert len(contexto["avisos"]) == 1 and "docs/sumiu.jpg" in contexto["avisos"][0]

    contexto = {"capa_fundo_storage_key": "docs/capa.txt"}
    ctx_mod.anexar_imagens_do_storage(contexto, storage)
    assert "capa_fundo_data_uri" not in contexto and "não é uma imagem" in contexto["avisos"][0]

    class StorageQuebrado(FakeStorage):
        def download(self, key):
            raise RuntimeError("MinIO fora do ar")

    contexto = {"assinatura_storage_key": "a.png"}
    ctx_mod.anexar_imagens_do_storage(contexto, StorageQuebrado())
    assert "RuntimeError" in contexto["avisos"][0]


# --- integração (PostgreSQL) -------------------------------------------------------


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def cenario():
    sufixo = uuid.uuid4().hex[:8]
    chaves = {
        "foto1": f"fotos/v105-{sufixo}-1.jpg",
        "foto2": f"fotos/v105-{sufixo}-2.jpg",
        "foto_ia": f"fotos/v105-{sufixo}-ia.jpg",
        "foto3": f"fotos/v105-{sufixo}-3.jpg",
        "assinatura": f"responsaveis/v105-{sufixo}/assinatura.png",
        "capa": f"edificacoes/v105-{sufixo}/documentos/capa.jpg",
    }
    async with _TestSessionLocal() as s:
        auditor = Usuario(
            nome="Auditor V1-05",
            email=f"auditor-v105-{sufixo}@garra.com",
            senha_hash=hash_password("senha-forte-123"),
            ativo=True,
            role="auditor",
        )
        fiscal = Responsavel(
            nome="Fiscal V1-05",
            tipo="fiscal",
            crea="1020304050/D-GO",
            email="fiscal-v105@example.com",
            telefone="(62) 90000-0000",
            titulo_profissional="Engenheiro Civil",
            qualificacoes=["Perito em Engenharia Diagnóstica"],
            assinatura_storage_key=chaves["assinatura"],
        )
        fiscal_sem_crea = Responsavel(nome="Fiscal sem CREA V1-05", tipo="fiscal")
        edificacao = Edificacao(
            nome=f"Residencial V1-05 {sufixo}",
            endereco="Rua 10, nº 200 - Setor Oeste, Goiânia - GO",
            cep="74000-000",
            tipologia="Residencial multifamiliar",
            sistema_construtivo="Concreto armado e alvenaria de vedação",
            descricao_pavimentos="Térreo, 2 subsolos e 20 pavimentos tipo",
            area_total_m2=15000.0,
            documentos_tecnicos={"itens": [{"nome": "capa.jpg", "tipo": "Capa", "storage_key": chaves["capa"]}]},
        )
        sistemas = [
            SistemaPredial(nome=f"Esquadrias V1-05 {sufixo}", ordem=9002),
            SistemaPredial(nome=f"Estrutura V1-05 {sufixo}", ordem=9001),
        ]
        s.add_all([auditor, fiscal, fiscal_sem_crea, edificacao, *sistemas])
        await s.commit()

        contratos = {
            nome: Contrato(
                edificacao_id=edificacao.id,
                fiscal_id=(fiscal_sem_crea if nome == "sem_crea" else fiscal).id,
                numero=f"CT-V105-{nome}-{sufixo}",
                tipo_servico=TIPO,
                status="em_andamento",
            )
            for nome in ("completo", "sem_unidade", "sem_crea")
        }
        s.add_all(contratos.values())
        await s.commit()
        inspecoes = {
            nome: Inspecao(contrato_id=c.id, tipo=TIPO, status="em_andamento") for nome, c in contratos.items()
        }
        s.add_all(inspecoes.values())
        await s.commit()

        completa = inspecoes["completo"].id
        estrutura, esquadrias = sistemas[1], sistemas[0]
        oc1 = Ocorrencia(
            inspecao_id=completa,
            sistema_id=esquadrias.id,
            situacao="aberta",
            classificacao="anomalia",
            localizacao="Sala",
            descricao="Folga na esquadria da janela",
            seq_numero=1,
        )
        oc2 = Ocorrencia(
            inspecao_id=completa,
            sistema_id=estrutura.id,
            situacao="aberta",
            classificacao="anomalia",
            localizacao="Laje do quarto",
            descricao="Fissura & infiltração <visível>",
            seq_numero=2,
        )
        s.add_all([oc1, oc2])
        await s.commit()
        s.add_all([
            Foto(ocorrencia_id=oc1.id, storage_key=chaves["foto1"], origem="upload", legenda="Janela da sala", ordem=1),
            Foto(ocorrencia_id=oc2.id, storage_key=chaves["foto2"], origem="upload", legenda="Fissura na laje", ordem=2),
            # Sugestão de IA ainda em rascunho, sem legenda aprovada: não pode ir para o laudo.
            Foto(
                ocorrencia_id=oc2.id,
                storage_key=chaves["foto_ia"],
                origem="upload",
                legenda=None,
                legenda_ia_sugerida=SUGESTAO_IA,
                status_validacao_ia="rascunho",
                ordem=1,
            ),
        ])
        s.add_all([
            RelatorioConteudo(
                inspecao_id=completa,
                tipo=TIPO,
                dados={
                    "unidade": "Apartamento 101",
                    "data_emissao": "2026-11-10",
                    "datas_vistorias": ["2026-11-04"],
                    "fundamentacao_tecnica": {str(estrutura.id): ["ABNT NBR 15575-2."]},
                    "textos": {"s10": ["Conclusão escrita pelo auditor."]},
                },
            ),
            RelatorioConteudo(inspecao_id=inspecoes["sem_crea"].id, tipo=TIPO, dados={"unidade": "Ap. 2"}),
        ])
        await s.commit()

        yield {
            "auditor": auditor,
            "inspecoes": {nome: i.id for nome, i in inspecoes.items()},
            "chaves": chaves,
            "sistemas": {"estrutura": estrutura.id, "esquadrias": esquadrias.id},
        }

        ids = [i.id for i in inspecoes.values()]
        await s.execute(delete(Relatorio).where(Relatorio.inspecao_id.in_(ids)))
        await s.execute(delete(RelatorioConteudo).where(RelatorioConteudo.inspecao_id.in_(ids)))
        await s.execute(delete(Foto).where(Foto.ocorrencia_id.in_([oc1.id, oc2.id])))
        await s.execute(delete(Ocorrencia).where(Ocorrencia.inspecao_id.in_(ids)))
        await s.execute(delete(Inspecao).where(Inspecao.id.in_(ids)))
        await s.execute(delete(Contrato).where(Contrato.id.in_([c.id for c in contratos.values()])))
        await s.execute(delete(SistemaPredial).where(SistemaPredial.id.in_([x.id for x in sistemas])))
        await s.execute(delete(Edificacao).where(Edificacao.id == edificacao.id))
        await s.execute(delete(Responsavel).where(Responsavel.id.in_([fiscal.id, fiscal_sem_crea.id])))
        await s.execute(delete(Usuario).where(Usuario.id == auditor.id))
        await s.commit()


async def _montar(inspecao_id) -> dict:
    async with _TestSessionLocal() as s:
        return await ctx_mod.montar_contexto_vistoria_residencial(s, inspecao_id)


@pytest.mark.asyncio
async def test_contexto_do_banco_passa_no_normalizar_e_renderiza(cenario):
    contexto = await _montar(cenario["inspecoes"]["completo"])

    assert ctx_mod.validar_contexto_vistoria_residencial(contexto) == []
    assert contexto["imovel"] == {"unidade": "Apartamento 101"}
    assert contexto["fiscal"]["qualificacoes"] == ["Perito em Engenharia Diagnóstica"]
    assert contexto["data_emissao"] == date(2026, 11, 10)
    assert contexto["local_emissao"] == "Goiânia-GO"
    assert contexto["assinatura_storage_key"] == cenario["chaves"]["assinatura"]
    assert contexto["capa_fundo_storage_key"] == cenario["chaves"]["capa"]

    # Fotos numeradas na ordem das ocorrências (seq) e, dentro delas, por `ordem`.
    chaves = cenario["chaves"]
    assert [(f["numero"], f["storage_key"]) for f in contexto["fotos"]] == [
        (1, chaves["foto1"]),
        (2, chaves["foto_ia"]),
        (3, chaves["foto2"]),
    ]
    assert {f["fonte"] for f in contexto["fotos"]} == {"Autor"}

    # Sistemas pela ordem do gabarito; fundamentação vem do conteúdo salvo.
    assert [s["id"] for s in contexto["sistemas"]] == [
        str(cenario["sistemas"]["estrutura"]),
        str(cenario["sistemas"]["esquadrias"]),
    ]
    estrutura, esquadrias = contexto["sistemas"]
    assert estrutura["constatacoes"] == ["Laje do quarto: Fissura & infiltração <visível> (Figuras 2, 3)."]
    assert estrutura["fundamentacao_tecnica"] == ["ABNT NBR 15575-2."]
    assert esquadrias["constatacoes"] == ["Sala: Folga na esquadria da janela (Figura 1)."]
    assert esquadrias["fundamentacao_tecnica"] == []

    assert contexto["textos"]["s5_2"] == ["A vistoria foi realizada em 04/11/2026."]
    assert contexto["textos"]["s5_1"][0].startswith("A inspeção foi realizada pelo responsável técnico Fiscal V1-05")
    assert contexto["textos"]["s10"] == ["Conclusão escrita pelo auditor."]
    assert "{edificacao_nome}" not in str(contexto["textos"])

    normalizado = pipeline.normalizar_contexto(contexto)
    assert set(normalizado["textos"]) == set(pipeline.TEXTOS_CHAVES)
    assert normalizado["data_emissao"] == "10/11/2026"
    assert esquadrias["nome"] == normalizado["sistemas"][1]["nome"]
    assert normalizado["sistemas"][1]["fundamentacao_tecnica"] == [pipeline.VAZIO]

    fotos_bytes = {k: _imagem("JPEG") for k in ctx_mod.extrair_fotos_vistoria_residencial(contexto)}
    html = pipeline.renderizar_html(contexto, fotos_bytes)
    texto = re.sub(r"<[^>]+>", " ", html)
    assert "None" not in texto
    assert "{{" not in html and "{%" not in html
    assert "Apartamento 101" in texto and "Fissura &amp; infiltração &lt;visível&gt;" in html


@pytest.mark.asyncio
async def test_s4_2_x_gerados_da_edificacao(cenario):
    contexto = await _montar(cenario["inspecoes"]["completo"])
    textos = contexto["textos"]
    assert textos["s4_2_1"] == ["Tipologia da edificação: Residencial multifamiliar."]
    assert textos["s4_2_2"] == [
        "Sistema construtivo: Concreto armado e alvenaria de vedação.",
        "Pavimentos: Térreo, 2 subsolos e 20 pavimentos tipo.",
        "Área total construída: 15.000 m².",
    ]
    assert textos["s4_2_3"] == ["Endereço: Rua 10, nº 200 - Setor Oeste, Goiânia - GO.", "CEP: 74000-000."]


@pytest.mark.asyncio
async def test_texto_salvo_prevalece_sobre_o_gerado(cenario):
    inspecao_id = cenario["inspecoes"]["completo"]
    async with _TestSessionLocal() as s:
        conteudo = (
            await s.execute(select(RelatorioConteudo).where(RelatorioConteudo.inspecao_id == inspecao_id))
        ).scalar_one()
        conteudo.dados = {**conteudo.dados, "textos": {"s4_2_1": ["Tipologia escrita pelo auditor."]}}
        await s.commit()
    contexto = await _montar(inspecao_id)
    assert contexto["textos"]["s4_2_1"] == ["Tipologia escrita pelo auditor."]
    assert contexto["textos"]["s4_2_2"][0].startswith("Sistema construtivo:")


@pytest.mark.asyncio
async def test_legenda_nao_aprovada_nao_entra(cenario):
    contexto = await _montar(cenario["inspecoes"]["completo"])
    foto_ia = next(f for f in contexto["fotos"] if f["storage_key"] == cenario["chaves"]["foto_ia"])
    assert foto_ia["legenda"] is None
    assert SUGESTAO_IA not in str(contexto)
    normalizado = pipeline.normalizar_contexto(contexto)
    assert normalizado["fotos"][1]["legenda"] == pipeline.VAZIO
    assert SUGESTAO_IA not in str(normalizado)


@pytest.mark.asyncio
async def test_sem_conteudo_usa_padroes(cenario):
    contexto = await _montar(cenario["inspecoes"]["sem_unidade"])
    assert contexto["imovel"]["unidade"] == "—"
    assert contexto["data_emissao"] == ctx_mod.hoje()
    assert contexto["fotos"] == [] and contexto["sistemas"] == []
    assert contexto["textos"]["s5_2"] == []
    assert contexto["textos"]["s1_1"][0].count("Residencial V1-05") == 1
    assert ctx_mod.validar_contexto_vistoria_residencial(contexto) == ["imovel.unidade"]


@pytest.fixture
def api(cenario):
    chaves = cenario["chaves"]
    storage = FakeStorage({
        chaves["foto1"]: _imagem("JPEG"),
        chaves["foto2"]: _imagem("JPEG"),
        chaves["foto_ia"]: _imagem("JPEG"),
        chaves["assinatura"]: _imagem("PNG"),
        # sem a capa: o storage "falha" e a emissão segue com aviso
    })
    renderizador = FakeRenderizador()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_storage_client] = lambda: storage
    app.dependency_overrides[get_renderizador_por_tipo] = lambda: (lambda tipo: renderizador)
    yield TestClient(app), storage, renderizador
    for dep in (get_storage_client, get_renderizador_por_tipo):
        app.dependency_overrides.pop(dep, None)


def _url(inspecao_id) -> str:
    return f"/api/v1/inspecoes/{inspecao_id}/relatorios/{TIPO}"


def test_post_cria_versao_1(api, cenario):
    client, storage, renderizador = api
    inspecao_id = cenario["inspecoes"]["completo"]

    response = client.post(_url(inspecao_id), headers=_auth(cenario["auditor"]))

    assert response.status_code == 201, response.text
    corpo = response.json()
    assert corpo["versao"] == "V01"
    assert corpo["tipo"] == TIPO
    pdf_key = f"relatorios/{inspecao_id}/vistoria_residencial-v01.pdf"
    assert storage.objetos[pdf_key] == b"%PDF-1.7 fake"
    assert f"relatorios/{inspecao_id}/vistoria_residencial-v01.docx" in storage.objetos

    _, contexto, fotos_bytes = renderizador.chamadas[0]
    chaves = cenario["chaves"]
    assert set(fotos_bytes) == {chaves["foto1"], chaves["foto2"], chaves["foto_ia"]}
    assert contexto["assinatura_data_uri"].startswith("data:image/png;base64,")
    assert contexto["capa_fundo_data_uri"] is None
    assert any(chaves["capa"] in aviso for aviso in contexto["avisos"])


def test_post_sem_unidade_retorna_422(api, cenario):
    client, _, renderizador = api
    response = client.post(_url(cenario["inspecoes"]["sem_unidade"]), headers=_auth(cenario["auditor"]))
    assert response.status_code == 422
    corpo = response.json()
    assert corpo["type"].endswith("/vistoria_residencial-contexto-incompleto")
    assert [e["field"] for e in corpo["errors"]] == ["imovel.unidade"]
    assert renderizador.chamadas == []


def test_post_sem_crea_do_fiscal_retorna_422(api, cenario):
    client, _, renderizador = api
    response = client.post(_url(cenario["inspecoes"]["sem_crea"]), headers=_auth(cenario["auditor"]))
    assert response.status_code == 422
    assert [e["field"] for e in response.json()["errors"]] == ["fiscal.crea"]
    assert renderizador.chamadas == []
