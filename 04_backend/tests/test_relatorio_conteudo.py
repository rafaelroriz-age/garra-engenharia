"""Testes da fundação de dados da emissão (V1-01).

- enum `TipoServico` (normaliza minúsculas) nos schemas de Contrato/Inspeção;
- `GET/PUT /api/v1/inspecoes/{id}/conteudo/{tipo}` (padrões, deep merge, RBAC, tetos);
- textos padrão com as chaves exatas dos pipelines;
- campos novos do Responsável.

Os testes de API exigem o PostgreSQL de 05_infra/docker-compose.yml (localhost:5433)
com a migration `a9c3e5f7b1d2` aplicada; os de unidade não usam banco.
"""
import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Contrato, Edificacao, Inspecao, RelatorioConteudo, Responsavel, Usuario
from app.models.tipo_servico import TipoServico
from app.schemas.contrato import ContratoCreatePayload, ContratoRead
from app.schemas.inspecao import InspecaoCreate
from app.schemas.relatorio_conteudo import DADOS_MAX_CARACTERES, TEXTO_MAX, ConteudoDados
from app.services import relatorio_conteudo_service as servico
from app.services.report_generator.ltip_pipeline import SECOES_TEXTO
from app.services.report_generator.vistoria_residencial_pipeline import TEXTOS_CHAVES

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


# --------------------------------------------------------------------------- unidade


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("ltip", TipoServico.LTIP), (" rfo ", TipoServico.RFO), ("Vistoria_Cautelar", TipoServico.VISTORIA_CAUTELAR)],
)
def test_enum_normaliza_minusculas(entrada, esperado):
    assert TipoServico(entrada) is esperado
    assert TipoServico.normalizar(entrada) is esperado


def test_enum_rejeita_tipo_desconhecido():
    assert TipoServico.normalizar("Fiscalização de obra") is None
    assert TipoServico.normalizar(None) is None
    with pytest.raises(ValueError):
        TipoServico("fiscalizacao")


def test_schemas_de_entrada_validam_e_normalizam_tipo():
    payload = ContratoCreatePayload(
        edificacao_id=uuid.uuid4(),
        fiscal_id=uuid.uuid4(),
        numero="CT-1",
        tipo_servico="vistoria_residencial",
        art_fiscalizacao="ART-1",
        executores=[
            {"responsavel_legal_id": str(uuid.uuid4()), "razao_social": "X", "cnpj": "1", "art_execucao": "A"}
        ],
    )
    assert payload.tipo_servico == "VISTORIA_RESIDENCIAL"
    assert type(payload.model_dump()["tipo_servico"]) is str  # o modelo grava texto puro
    assert InspecaoCreate(contrato_id=uuid.uuid4(), tipo="rfip", status="x").tipo == "RFIP"
    with pytest.raises(ValidationError):
        InspecaoCreate(contrato_id=uuid.uuid4(), tipo="Fiscalização de obra", status="x")


def test_leitura_tolera_valor_legado():
    """Valor gravado antes de V1-01 não derruba a listagem (sai como texto)."""
    from datetime import datetime

    lido = ContratoRead(
        id=uuid.uuid4(),
        created_at=datetime.now(),
        edificacao_id=uuid.uuid4(),
        fiscal_id=uuid.uuid4(),
        numero="CT-L",
        tipo_servico="FISCALIZAÇÃO DE OBRA",
        status="em_andamento",
    )
    assert lido.tipo_servico == "FISCALIZAÇÃO DE OBRA"


def test_textos_padrao_tem_as_chaves_exatas_dos_pipelines():
    import re
    from pathlib import Path

    assert set(servico.textos_padrao(TipoServico.LTIP)) == set(SECOES_TEXTO)
    assert set(servico.textos_padrao(TipoServico.VISTORIA_RESIDENCIAL)) == set(TEXTOS_CHAVES)
    template = (
        Path(__file__).resolve().parents[1] / "templates" / "vistoria_cautelar" / "vistoria_cautelar_template.html.j2"
    ).read_text(encoding="utf-8")
    chaves_cautelar = set(re.findall(r"conteudo\.get\('([a-z_0-9]+)'", template))
    assert set(servico.textos_padrao(TipoServico.VISTORIA_CAUTELAR)) == chaves_cautelar
    assert servico.textos_padrao(TipoServico.RFO) == {}
    assert servico.textos_padrao(TipoServico.RFIP) == {}
    for tipo in TipoServico:
        for paragrafos in servico.textos_padrao(tipo).values():
            assert all(isinstance(p, str) and p.strip() for p in paragrafos)


def test_textos_padrao_sem_dados_do_cliente_original():
    proibidos = ("Cortina", "New York", "Urbânica", "Opus Gyro", "1404", "Roniel", "Natália Borges")
    for tipo in TipoServico:
        texto = str(servico.textos_padrao(tipo))
        for termo in proibidos:
            assert termo not in texto, f"{tipo}: '{termo}' nos textos padrão"


def test_deep_merge_e_placeholders():
    base = {"textos": {"a": ["x"], "b": ["y"]}, "local_emissao": "A"}
    sobre = {"textos": {"a": []}, "local_emissao": "B", "parecer": "P"}
    assert servico.deep_merge(base, sobre) == {
        "textos": {"a": [], "b": ["y"]},
        "local_emissao": "B",
        "parecer": "P",
    }
    assert base["textos"]["a"] == ["x"]  # não muta
    preenchido = servico.preencher_placeholders(
        {"k": ["Ed. {edificacao_nome} em {edificacao_endereco} {outro}"]}, {"edificacao_nome": "Alfa"}
    )
    assert preenchido == {"k": ["Ed. Alfa em — {outro}"]}


def test_dados_texto_livre_vira_paragrafos_e_campos_extras_sao_rejeitados():
    dados = ConteudoDados(textos={"objetivo": "linha 1\n\n linha 2 "})
    assert dados.textos == {"objetivo": ["linha 1", "linha 2"]}
    with pytest.raises(ValidationError):
        ConteudoDados(campo_inexistente="x")
    with pytest.raises(ValidationError):
        ConteudoDados(textos={"Chave Invalida": ["x"]})


# --------------------------------------------------------------------------- API (banco)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


def _auth(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(usuario.id))}"}


@pytest_asyncio.fixture
async def cenario():
    sufixo = uuid.uuid4().hex[:8]
    async with _TestSessionLocal() as s:
        usuarios = {
            role: Usuario(
                nome=f"{role} V1-01",
                email=f"{role}-v101-{sufixo}@garra.com",
                senha_hash=hash_password("senha-forte-123"),
                ativo=True,
                role=role,
            )
            for role in ("auditor", "auxiliar")
        }
        s.add_all(usuarios.values())
        fiscal = Responsavel(nome="Fiscal V1-01", tipo="fiscal")
        edificacao = Edificacao(nome=f"Edifício Teste {sufixo}", endereco="Rua V1, 1")
        s.add_all([fiscal, edificacao])
        await s.commit()
        contrato = Contrato(
            edificacao_id=edificacao.id,
            fiscal_id=fiscal.id,
            numero=f"CT-V101-{sufixo}",
            tipo_servico="LTIP",
            status="em_andamento",
        )
        s.add(contrato)
        await s.commit()
        inspecao = Inspecao(contrato_id=contrato.id, tipo="LTIP", status="em_andamento")
        s.add(inspecao)
        await s.commit()

        yield {"usuarios": usuarios, "inspecao_id": inspecao.id, "edificacao_nome": edificacao.nome}

        await s.execute(delete(RelatorioConteudo).where(RelatorioConteudo.inspecao_id == inspecao.id))
        await s.execute(delete(Inspecao).where(Inspecao.id == inspecao.id))
        await s.execute(delete(Contrato).where(Contrato.id == contrato.id))
        await s.execute(delete(Edificacao).where(Edificacao.id == edificacao.id))
        await s.execute(delete(Responsavel).where(Responsavel.id == fiscal.id))
        await s.execute(delete(Usuario).where(Usuario.id.in_([u.id for u in usuarios.values()])))
        await s.commit()


def _url(inspecao_id, tipo="LTIP") -> str:
    return f"/api/v1/inspecoes/{inspecao_id}/conteudo/{tipo}"


@pytest.mark.parametrize("role", ["auditor", "auxiliar"])
async def test_get_devolve_padroes_com_placeholder_preenchido(client, cenario, role):
    resposta = client.get(_url(cenario["inspecao_id"]), headers=_auth(cenario["usuarios"][role]))
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["tipo"] == "LTIP"
    assert corpo["salvo"] is False
    assert corpo["atualizado_em"] is None
    textos = corpo["dados"]["textos"]
    assert set(textos) == set(SECOES_TEXTO)
    assert cenario["edificacao_nome"] in textos["introducao"][0]
    assert "{edificacao_nome}" not in str(textos)


async def test_get_aceita_tipo_minusculo_e_404_sem_inspecao(client, cenario):
    auditor = cenario["usuarios"]["auditor"]
    resposta = client.get(_url(cenario["inspecao_id"], "vistoria_cautelar"), headers=_auth(auditor))
    assert resposta.status_code == 200
    assert resposta.json()["tipo"] == "VISTORIA_CAUTELAR"
    assert client.get(_url(cenario["inspecao_id"], "XPTO"), headers=_auth(auditor)).status_code == 422
    assert client.get(_url(uuid.uuid4()), headers=_auth(auditor)).status_code == 404


async def test_get_sem_token_401(client, cenario):
    assert client.get(_url(cenario["inspecao_id"])).status_code == 401


async def test_put_do_auditor_salva_e_get_mescla(client, cenario):
    auditor = cenario["usuarios"]["auditor"]
    ocorrencia_id = str(uuid.uuid4())
    sistema_id = str(uuid.uuid4())
    payload = {
        "dados": {
            "textos": {"introducao": ["Texto editado."], "conclusao": "Linha A\nLinha B"},
            "data_emissao": "2026-11-10",
            "local_emissao": "Goiânia-GO",
            "parecer": "Favorável com ressalvas.",
            "datas_vistorias": ["2026-10-01", "2026-10-08"],
            "metodologia_corretiva": {ocorrencia_id: "Refazer rejunte."},
            "fundamentacao_tecnica": {sistema_id: ["NBR 13753."]},
        }
    }
    resposta = client.put(_url(cenario["inspecao_id"]), json=payload, headers=_auth(auditor))
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["salvo"] is True

    corpo = client.get(_url(cenario["inspecao_id"]), headers=_auth(cenario["usuarios"]["auxiliar"])).json()
    dados = corpo["dados"]
    assert corpo["salvo"] is True
    assert corpo["atualizado_por_id"] == str(auditor.id)
    assert dados["textos"]["introducao"] == ["Texto editado."]
    assert dados["textos"]["conclusao"] == ["Linha A", "Linha B"]
    assert dados["textos"]["objetivo"] == servico.textos_padrao(TipoServico.LTIP)["objetivo"]  # padrão mantido
    assert dados["data_emissao"] == "2026-11-10"
    assert dados["local_emissao"] == "Goiânia-GO"
    assert dados["datas_vistorias"] == ["2026-10-01", "2026-10-08"]
    assert dados["metodologia_corretiva"] == {ocorrencia_id: "Refazer rejunte."}
    assert dados["fundamentacao_tecnica"] == {sistema_id: ["NBR 13753."]}

    # PUT substitui o salvo (upsert): o que não vier volta ao padrão.
    segundo = client.put(
        _url(cenario["inspecao_id"]), json={"dados": {"incluir_resumo": True}}, headers=_auth(auditor)
    )
    assert segundo.status_code == 200
    dados = segundo.json()["dados"]
    assert dados["incluir_resumo"] is True
    assert "parecer" not in dados
    assert dados["textos"]["introducao"] == client.get(
        _url(cenario["inspecao_id"]), headers=_auth(auditor)
    ).json()["dados"]["textos"]["introducao"]
    assert dados["textos"]["introducao"] != ["Texto editado."]

    # O conteúdo é por tipo: outro tipo da mesma inspeção continua só com padrões.
    outro = client.get(_url(cenario["inspecao_id"], "RFIP"), headers=_auth(auditor)).json()
    assert outro["salvo"] is False
    assert outro["dados"] == {"textos": {}}


async def test_put_do_auxiliar_403(client, cenario):
    resposta = client.put(
        _url(cenario["inspecao_id"]),
        json={"dados": {"parecer": "x"}},
        headers=_auth(cenario["usuarios"]["auxiliar"]),
    )
    assert resposta.status_code == 403


@pytest.mark.parametrize(
    "dados",
    [
        {"parecer": "x" * (TEXTO_MAX + 1)},
        {"textos": {"introducao": ["y" * (TEXTO_MAX + 1)]}},
        {"textos": {chave: ["z" * TEXTO_MAX] * 5 for chave in SECOES_TEXTO}},  # > DADOS_MAX_CARACTERES
        {"campo_desconhecido": "x"},
        {"textos": {"chave_que_o_ltip_nao_tem": ["x"]}},
    ],
    ids=["texto-acima-do-teto", "paragrafo-acima-do-teto", "total-acima-do-teto", "campo-extra", "chave-invalida"],
)
async def test_put_invalido_ou_acima_do_teto_422(client, cenario, dados):
    assert 7 * 5 * TEXTO_MAX > DADOS_MAX_CARACTERES
    resposta = client.put(
        _url(cenario["inspecao_id"]), json={"dados": dados}, headers=_auth(cenario["usuarios"]["auditor"])
    )
    assert resposta.status_code == 422, resposta.text
    get = client.get(_url(cenario["inspecao_id"]), headers=_auth(cenario["usuarios"]["auditor"]))
    assert get.json()["salvo"] is False  # nada foi gravado


async def test_put_em_inspecao_inexistente_404(client, cenario):
    resposta = client.put(
        _url(uuid.uuid4()), json={"dados": {}}, headers=_auth(cenario["usuarios"]["auditor"])
    )
    assert resposta.status_code == 404


async def test_responsavel_expoe_campos_de_assinatura(client, cenario):
    auditor = cenario["usuarios"]["auditor"]
    resposta = client.post(
        "/api/v1/responsaveis",
        json={
            "nome": "Eng. Assinatura V1-01",
            "tipo": "fiscal",
            "titulo_profissional": "Engenheiro Civil",
            "qualificacoes": ["Membro titular do IBAPE-GO", "Especialista em Perícias"],
            "assinatura_storage_key": "assinaturas/teste.png",
        },
        headers=_auth(auditor),
    )
    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    try:
        assert corpo["titulo_profissional"] == "Engenheiro Civil"
        assert corpo["qualificacoes"] == ["Membro titular do IBAPE-GO", "Especialista em Perícias"]
        assert corpo["assinatura_storage_key"] == "assinaturas/teste.png"
        lido = client.get(f"/api/v1/responsaveis/{corpo['id']}", headers=_auth(auditor)).json()
        assert lido["qualificacoes"] == corpo["qualificacoes"]
    finally:
        async with _TestSessionLocal() as s:
            await s.execute(delete(Responsavel).where(Responsavel.id == uuid.UUID(corpo["id"])))
            await s.commit()
