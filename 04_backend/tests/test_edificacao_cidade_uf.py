"""`cidade`/`uf` em Edificação e o local de emissão dos relatórios (DEC-50 P5).

- API: criação, atualização (PUT substitui) e leitura com e sem os campos; `uf` normalizada para
  maiúsculas, vazio vira `None`, `uf` inválida → 422 (RFC 7807, DEC-11).
- `contexto_comum.cidade_emissao`: cidade+uf, só uma delas e nenhuma (fallback pelo endereço),
  com os parsers dos dois montadores de vistoria.
- Montadores de vistoria (cautelar e residencial) no banco: `local_emissao` vem de cidade/uf
  quando preenchidas e do endereço quando ausentes.
"""
import uuid
from types import SimpleNamespace

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
from app.models import Contrato, Edificacao, Inspecao, Responsavel, Usuario
from app.models.tipo_servico import TipoServico
from app.services.report_generator import vistoria_cautelar_contexto as cautelar
from app.services.report_generator import vistoria_residencial_contexto as residencial
from app.services.report_generator.contexto_comum import cidade_emissao

_settings = get_settings()
_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool, future=True)
_TestSessionLocal = async_sessionmaker(bind=_test_engine, expire_on_commit=False)

ENDERECO_GOIANIA = "Rua Teste, 10, Setor Sul, Goiânia-GO, 74000-000"


async def _override_get_db():
    async with _TestSessionLocal() as session:
        yield session


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app)


@pytest_asyncio.fixture
async def auth_headers():
    email = f"cidade-uf-{uuid.uuid4()}@garra-engenharia.com.br"
    async with _TestSessionLocal() as session:
        usuario = Usuario(nome="Teste DEC-50", email=email, senha_hash=hash_password("senha-forte"), ativo=True)
        session.add(usuario)
        await session.commit()
        usuario_id = usuario.id
    yield {"Authorization": f"Bearer {create_access_token(subject=str(usuario_id))}"}
    async with _TestSessionLocal() as session:
        await session.execute(delete(Usuario).where(Usuario.id == usuario_id))
        await session.commit()


@pytest_asyncio.fixture
async def criadas():
    """Ids das edificações criadas pela API no teste, apagadas ao final."""
    ids: list[str] = []
    yield ids
    if ids:
        async with _TestSessionLocal() as session:
            await session.execute(delete(Edificacao).where(Edificacao.id.in_([uuid.UUID(i) for i in ids])))
            await session.commit()


def _criar(client, auth_headers, criadas, **extra):
    corpo = {"nome": f"Ed. DEC-50 {uuid.uuid4()}", "endereco": ENDERECO_GOIANIA, **extra}
    resposta = client.post("/api/v1/edificacoes", json=corpo, headers=auth_headers)
    if resposta.status_code == 201:
        criadas.append(resposta.json()["id"])
    return resposta


# --- API ------------------------------------------------------------------------------


def test_criar_sem_cidade_uf_continua_valido(client, auth_headers, criadas):
    resposta = _criar(client, auth_headers, criadas)
    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["cidade"] is None
    assert corpo["uf"] is None


def test_criar_com_cidade_uf_normaliza_e_le(client, auth_headers, criadas):
    resposta = _criar(client, auth_headers, criadas, cidade="  Anápolis ", uf=" go ")
    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["cidade"] == "Anápolis"
    assert corpo["uf"] == "GO"

    detalhe = client.get(f"/api/v1/edificacoes/{corpo['id']}", headers=auth_headers)
    assert detalhe.status_code == 200
    assert (detalhe.json()["cidade"], detalhe.json()["uf"]) == ("Anápolis", "GO")


def test_string_vazia_vira_none(client, auth_headers, criadas):
    resposta = _criar(client, auth_headers, criadas, cidade="", uf="   ")
    assert resposta.status_code == 201, resposta.text
    assert (resposta.json()["cidade"], resposta.json()["uf"]) == (None, None)


@pytest.mark.parametrize("uf", ["G", "GOI", "G1", "1A", "Ç1", "--"])
def test_uf_invalida_retorna_422(client, auth_headers, criadas, uf):
    resposta = _criar(client, auth_headers, criadas, uf=uf)
    assert resposta.status_code == 422, resposta.text
    assert resposta.headers["content-type"].startswith("application/problem+json")


def test_cidade_acima_de_120_retorna_422(client, auth_headers, criadas):
    resposta = _criar(client, auth_headers, criadas, cidade="X" * 121)
    assert resposta.status_code == 422, resposta.text


def test_atualizar_define_e_remove_cidade_uf(client, auth_headers, criadas):
    edificacao_id = _criar(client, auth_headers, criadas).json()["id"]
    base = {"nome": "Ed. DEC-50 atualizada", "endereco": ENDERECO_GOIANIA}

    resposta = client.put(
        f"/api/v1/edificacoes/{edificacao_id}", json={**base, "cidade": "Goiânia", "uf": "go"}, headers=auth_headers
    )
    assert resposta.status_code == 200, resposta.text
    assert (resposta.json()["cidade"], resposta.json()["uf"]) == ("Goiânia", "GO")

    # PUT substitui todos os campos (BL-08): sem cidade/uf no corpo, voltam a None.
    resposta = client.put(f"/api/v1/edificacoes/{edificacao_id}", json=base, headers=auth_headers)
    assert resposta.status_code == 200, resposta.text
    assert (resposta.json()["cidade"], resposta.json()["uf"]) == (None, None)


def test_atualizar_com_uf_invalida_retorna_422(client, auth_headers, criadas):
    edificacao_id = _criar(client, auth_headers, criadas).json()["id"]
    resposta = client.put(
        f"/api/v1/edificacoes/{edificacao_id}",
        json={"nome": "Ed.", "endereco": ENDERECO_GOIANIA, "uf": "XYZ"},
        headers=auth_headers,
    )
    assert resposta.status_code == 422, resposta.text


# --- contexto comum (puro) ------------------------------------------------------------


def _edif(endereco=ENDERECO_GOIANIA, cidade=None, uf=None):
    return SimpleNamespace(endereco=endereco, cidade=cidade, uf=uf)


PARSERS = [
    pytest.param(cautelar.cidade_do_endereco, id="parser-cautelar"),
    pytest.param(residencial.cidade_do_endereco, id="parser-residencial"),
]


@pytest.mark.parametrize("parser", PARSERS)
def test_cidade_e_uf_preenchidas_prevalecem_sobre_endereco(parser):
    assert cidade_emissao(_edif(cidade="Anápolis", uf="GO"), parser) == "Anápolis-GO"


@pytest.mark.parametrize("parser", PARSERS)
def test_ausentes_usa_fallback_pelo_endereco(parser):
    assert cidade_emissao(_edif(), parser) == parser(ENDERECO_GOIANIA) == "Goiânia-GO"


@pytest.mark.parametrize("parser", PARSERS)
def test_so_uf_usa_fallback_pelo_endereco(parser):
    assert cidade_emissao(_edif(uf="SP"), parser) == "Goiânia-GO"


@pytest.mark.parametrize("parser", PARSERS)
def test_so_cidade_igual_a_do_endereco_completa_a_uf(parser):
    assert cidade_emissao(_edif(cidade="goiânia"), parser) == "Goiânia-GO"


@pytest.mark.parametrize("parser", PARSERS)
def test_so_cidade_diferente_do_endereco_prevalece_sozinha(parser):
    assert cidade_emissao(_edif(cidade="Anápolis"), parser) == "Anápolis"


@pytest.mark.parametrize("parser", PARSERS)
def test_sem_nada_e_endereco_sem_cidade_devolve_none(parser):
    assert cidade_emissao(_edif(endereco="Rua A, 1"), parser) is None


def test_sem_parser_so_campos_explicitos_contam():
    assert cidade_emissao(_edif()) is None
    assert cidade_emissao(_edif(cidade="Anápolis", uf="go")) == "Anápolis-GO"
    assert cidade_emissao(_edif(cidade="Anápolis")) == "Anápolis"


def test_objeto_antigo_sem_atributos_cidade_uf():
    assert cidade_emissao(SimpleNamespace(endereco=ENDERECO_GOIANIA), cautelar.cidade_do_endereco) == "Goiânia-GO"


# --- montadores de vistoria no banco --------------------------------------------------


MONTADORES = [
    pytest.param(TipoServico.VISTORIA_CAUTELAR, cautelar.montar_contexto_vistoria_cautelar, id="cautelar"),
    pytest.param(TipoServico.VISTORIA_RESIDENCIAL, residencial.montar_contexto_vistoria_residencial, id="residencial"),
]


async def _cenario(tipo: TipoServico, cidade: str | None, uf: str | None) -> dict:
    sufixo = uuid.uuid4().hex[:8]
    async with _TestSessionLocal() as s:
        fiscal = Responsavel(nome="Eng. Fiscal DEC-50", tipo="fiscal", crea="1234567/D-GO")
        edificacao = Edificacao(nome=f"Ed. DEC-50 {sufixo}", endereco=ENDERECO_GOIANIA, cidade=cidade, uf=uf)
        s.add_all([fiscal, edificacao])
        await s.commit()
        contrato = Contrato(
            edificacao_id=edificacao.id,
            fiscal_id=fiscal.id,
            numero=f"CT-DEC50-{sufixo}",
            tipo_servico=tipo.value,
            status="em_andamento",
            objeto="Obra de teste",
        )
        s.add(contrato)
        await s.commit()
        inspecao = Inspecao(contrato_id=contrato.id, tipo=tipo.value, status="em_andamento")
        s.add(inspecao)
        await s.commit()
        return {"fiscal": fiscal.id, "edificacao": edificacao.id, "contrato": contrato.id, "inspecao": inspecao.id}


async def _apagar(ids: dict) -> None:
    async with _TestSessionLocal() as s:
        await s.execute(delete(Inspecao).where(Inspecao.id == ids["inspecao"]))
        await s.execute(delete(Contrato).where(Contrato.id == ids["contrato"]))
        await s.execute(delete(Edificacao).where(Edificacao.id == ids["edificacao"]))
        await s.execute(delete(Responsavel).where(Responsavel.id == ids["fiscal"]))
        await s.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize("tipo, montar", MONTADORES)
@pytest.mark.parametrize(
    "cidade, uf, esperado",
    [
        ("Anápolis", "GO", "Anápolis-GO"),
        (None, None, "Goiânia-GO"),
        (None, "SP", "Goiânia-GO"),
        ("Anápolis", None, "Anápolis"),
    ],
    ids=["cidade-uf", "ausentes-fallback", "so-uf", "so-cidade"],
)
async def test_montador_usa_cidade_uf_ou_endereco(tipo, montar, cidade, uf, esperado):
    ids = await _cenario(tipo, cidade, uf)
    try:
        async with _TestSessionLocal() as s:
            contexto = await montar(s, ids["inspecao"])
        assert contexto["local_emissao"] == esperado
    finally:
        await _apagar(ids)
