"""Lacunas de regras de Visitas/Equipe/Medições (revisão de BL-10 em T15; corrigidas em T21).

Cada `test_lacuna_*` afirma o comportamento CORRETO (DEC-38). Ver
`00_docs/backlog-auto/revisao-regras-visitas.md` (matriz) e `visitas-correcoes.md` (correção).
L15 segue `xfail` estrito: depende do vínculo usuário<->contrato (DEC-27), decisão do dono.
Regras: RF-03, RN-01, RN-02, RN-18 (`00_docs/estudo-do-contexto.md`), DEC-27, DEC-29.
"""
import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
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
    Responsavel,
    Usuario,
    Visita,
    VisitaMaoObra,
    VisitaMedicao,
)

_engine = create_async_engine(get_settings().database_url, poolclass=NullPool, future=True)
_Session = async_sessionmaker(bind=_engine, expire_on_commit=False)


async def _override_get_db():
    async with _Session() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db

# 500 não deve virar exceção no teste: queremos ver o status HTTP (lacuna de validação).
client = TestClient(app, raise_server_exceptions=False)


@pytest_asyncio.fixture
async def usuario_factory():
    criados: list[uuid.UUID] = []

    async def _criar(role: str) -> dict:
        async with _Session() as s:
            u = Usuario(
                nome=f"Lacuna {role}",
                email=f"lac-visitas-{uuid.uuid4()}@garra-engenharia.com.br",
                senha_hash=hash_password("senha-forte"),
                ativo=True,
                role=role,
            )
            s.add(u)
            await s.commit()
            await s.refresh(u)
            criados.append(u.id)
        return {"Authorization": f"Bearer {create_access_token(subject=str(u.id))}"}

    yield _criar

    async with _Session() as s:
        await s.execute(delete(Visita).where(Visita.criado_por_id.in_(criados)))
        await s.execute(delete(Usuario).where(Usuario.id.in_(criados)))
        await s.commit()


@pytest_asyncio.fixture
async def auth_headers(usuario_factory):
    return await usuario_factory("auditor")


@pytest_asyncio.fixture
async def inspecao_factory(db_session):
    criadas: list[tuple] = []

    async def _criar(tipo: str = "RFO") -> Inspecao:
        ed = Edificacao(nome=f"Ed. lacuna {uuid.uuid4()}", endereco="Rua das Lacunas, 1")
        fiscal = Responsavel(nome="Eng. Lacuna", tipo="fiscal", crea="333333-GO")
        db_session.add_all([ed, fiscal])
        await db_session.commit()
        ct = Contrato(
            edificacao_id=ed.id,
            fiscal_id=fiscal.id,
            numero=f"CT-LAC-{uuid.uuid4()}",
            tipo_servico="Fiscalização de obra",
            status="em_andamento",
            art_fiscalizacao="ART-LAC",
        )
        db_session.add(ct)
        await db_session.commit()
        insp = Inspecao(contrato_id=ct.id, tipo=tipo, status="em_andamento")
        db_session.add(insp)
        await db_session.commit()
        await db_session.refresh(insp)
        # Guarda só os ids: um rollback no teste (ex.: L5, IntegrityError) expira os objetos da
        # sessão, e ler `insp.id` expirado no teardown dispara lazy load síncrono (MissingGreenlet).
        criadas.append((insp.id, ct.id, fiscal.id, ed.id))
        return insp

    yield _criar

    await db_session.rollback()
    for insp_id, ct_id, fiscal_id, ed_id in criadas:
        ids = select(Visita.id).where(Visita.inspecao_id == insp_id)
        await db_session.execute(delete(VisitaMaoObra).where(VisitaMaoObra.visita_id.in_(ids)))
        await db_session.execute(delete(VisitaMedicao).where(VisitaMedicao.visita_id.in_(ids)))
        await db_session.execute(delete(Visita).where(Visita.inspecao_id == insp_id))
        await db_session.execute(delete(Inspecao).where(Inspecao.id == insp_id))
        await db_session.execute(delete(Contrato).where(Contrato.id == ct_id))
        await db_session.execute(delete(Responsavel).where(Responsavel.id == fiscal_id))
        await db_session.execute(delete(Edificacao).where(Edificacao.id == ed_id))
    await db_session.commit()


@pytest_asyncio.fixture
async def inspecao(inspecao_factory):
    return await inspecao_factory("RFO")


def _visita(inspecao_id, headers, data="2026-07-01") -> dict:
    r = client.post(
        f"/api/v1/inspecoes/{inspecao_id}/visitas",
        json={"data": data, "servicos_executados": "Fundação"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------- RN-01 / datas

def test_lacuna_1_visita_em_data_futura_deve_ser_rejeitada(auth_headers, inspecao):
    """RN-01/RN-02: a visita registra um dia de obra JÁ acompanhado; data futura é incoerente (esperado 422)."""
    futura = (date.today() + timedelta(days=30)).isoformat()
    r = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": futura, "servicos_executados": "Fundação"},
        headers=auth_headers,
    )
    assert r.status_code == 422, r.text


def test_lacuna_2_put_visita_em_data_futura_deve_ser_rejeitado(auth_headers, inspecao):
    """RN-01: atualização também não pode mover a visita para data futura (esperado 422)."""
    v = _visita(inspecao.id, auth_headers)
    futura = (date.today() + timedelta(days=30)).isoformat()
    r = client.put(
        f"/api/v1/visitas/{v['id']}",
        json={"data": futura, "servicos_executados": "Fundação"},
        headers=auth_headers,
    )
    assert r.status_code == 422, r.text


def test_lacuna_3_duas_visitas_no_mesmo_dia_devem_ser_rejeitadas(auth_headers, inspecao):
    """RN-01: 'uma Visita por dia de obra acompanhado' — segunda visita na mesma data da inspeção deve dar 409/422."""
    _visita(inspecao.id, auth_headers, "2026-07-01")
    r = client.post(
        f"/api/v1/inspecoes/{inspecao.id}/visitas",
        json={"data": "2026-07-01", "servicos_executados": "Alvenaria"},
        headers=auth_headers,
    )
    assert r.status_code in (409, 422), r.text


def test_lacuna_4_put_nao_pode_mover_visita_para_dia_ja_usado(auth_headers, inspecao):
    """RN-01: PUT que muda a data para um dia já ocupado por outra visita da inspeção deve dar 409/422."""
    _visita(inspecao.id, auth_headers, "2026-07-01")
    v2 = _visita(inspecao.id, auth_headers, "2026-07-02")
    r = client.put(
        f"/api/v1/visitas/{v2['id']}",
        json={"data": "2026-07-01", "servicos_executados": "Alvenaria"},
        headers=auth_headers,
    )
    assert r.status_code in (409, 422), r.text


async def test_lacuna_5_seq_numero_deve_ser_unico_por_inspecao_no_banco(inspecao, db_session):
    """RN-01: `seq_numero` é sequencial por inspeção; sem UNIQUE(inspecao_id, seq_numero) duas
    requisições concorrentes (max()+1 sem lock) geram duplicata. O banco deve recusar (IntegrityError)."""
    db_session.add(Visita(inspecao_id=inspecao.id, data=date(2026, 7, 1), servicos_executados="a", seq_numero=1))
    await db_session.commit()
    db_session.add(Visita(inspecao_id=inspecao.id, data=date(2026, 7, 2), servicos_executados="b", seq_numero=1))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.parametrize("tipo", ["LTIP", "VISTORIA"])
async def test_lacuna_6_visita_so_para_inspecao_rfo(auth_headers, inspecao_factory, tipo):
    """RF-03/RN-01: Visitas existem 'para RFO'; criar visita em inspeção LTIP/outro tipo deve dar 409/422."""
    insp = await inspecao_factory(tipo)
    r = client.post(
        f"/api/v1/inspecoes/{insp.id}/visitas",
        json={"data": "2026-07-01", "servicos_executados": "Algo"},
        headers=auth_headers,
    )
    assert r.status_code in (409, 422), r.text


# ---------------------------------------------------------------- RN-02 equipe

@pytest.mark.parametrize("qtd", [0, -3])
def test_lacuna_7_mao_obra_quantidade_deve_ser_positiva(auth_headers, inspecao, qtd):
    """RN-02: quantidade de profissionais é inteiro > 0 (esperado 422; hoje aceita 0 e negativos)."""
    v = _visita(inspecao.id, auth_headers)
    r = client.post(
        f"/api/v1/visitas/{v['id']}/mao-obra",
        json={"funcao": "Pedreiro", "quantidade": qtd},
        headers=auth_headers,
    )
    assert r.status_code == 422, r.text


def test_lacuna_8_mao_obra_quantidade_acima_do_int32_deve_dar_422_nao_500(auth_headers, inspecao):
    """Robustez: coluna Integer (32 bits); valor 2**40 estoura no PostgreSQL -> 500. Esperado 422."""
    v = _visita(inspecao.id, auth_headers)
    r = client.post(
        f"/api/v1/visitas/{v['id']}/mao-obra",
        json={"funcao": "Pedreiro", "quantidade": 2**40},
        headers=auth_headers,
    )
    assert r.status_code == 422, r.text


@pytest.mark.parametrize("funcao", ["", "   "])
def test_lacuna_9_mao_obra_funcao_obrigatoria(auth_headers, inspecao, funcao):
    """RN-02: a equipe é registrada por função + quantidade; função vazia/em branco deve dar 422."""
    v = _visita(inspecao.id, auth_headers)
    r = client.post(
        f"/api/v1/visitas/{v['id']}/mao-obra",
        json={"funcao": funcao, "quantidade": 2},
        headers=auth_headers,
    )
    assert r.status_code == 422, r.text


# ---------------------------------------------------------------- RF-03 medições / DEC-29

def test_lacuna_10_medicao_quantidade_negativa_deve_ser_rejeitada(auth_headers, inspecao):
    """RF-03: medição parcial de serviço executado não pode ter quantidade negativa (esperado 422)."""
    v = _visita(inspecao.id, auth_headers)
    r = client.post(
        f"/api/v1/visitas/{v['id']}/medicoes",
        json={"descricao": "Concreto", "quantidade": -5.0, "unidade": "m3"},
        headers=auth_headers,
    )
    assert r.status_code == 422, r.text


@pytest.mark.parametrize("campo", ["descricao", "unidade"])
@pytest.mark.parametrize("valor", ["", "   "])
def test_lacuna_11_medicao_descricao_e_unidade_nao_podem_ser_vazias(auth_headers, inspecao, campo, valor):
    """RF-03/DEC-29: unidade é LIVRE por item (texto), mas obrigatória e não vazia; descrição idem (esperado 422)."""
    v = _visita(inspecao.id, auth_headers)
    corpo = {"descricao": "Concreto", "quantidade": 1.0, "unidade": "m3", campo: valor}
    r = client.post(f"/api/v1/visitas/{v['id']}/medicoes", json=corpo, headers=auth_headers)
    assert r.status_code == 422, r.text


def test_lacuna_12_medicao_unidade_livre_deve_ser_aparada(auth_headers, inspecao):
    """DEC-29: unidade livre (m², verba, h) — espaços nas bordas devem ser removidos ('  m²  ' -> 'm²')."""
    v = _visita(inspecao.id, auth_headers)
    r = client.post(
        f"/api/v1/visitas/{v['id']}/medicoes",
        json={"descricao": "Reboco", "quantidade": 10, "unidade": "  m²  "},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["unidade"] == "m²"


# ---------------------------------------------------------------- RN-18 / DEC-27 permissões

@pytest.mark.parametrize(
    "metodo,rota,corpo",
    [
        ("put", "/api/v1/visitas/{v}", {"data": "2026-07-01", "servicos_executados": "x"}),
        ("post", "/api/v1/visitas/{v}/mao-obra", {"funcao": "Pedreiro", "quantidade": 1}),
        ("post", "/api/v1/visitas/{v}/medicoes", {"descricao": "x", "quantidade": 1, "unidade": "un"}),
    ],
)
async def test_lacuna_13_cliente_nao_escreve_em_visitas(auth_headers, usuario_factory, inspecao, metodo, rota, corpo):
    """RN-18/DEC-27: perfil `cliente` só acessa /portal/*; escrita em visitas deve dar 403.
    (Pode passar hoje, pois `require_equipe` bloqueia; o teste trava a regressão.)"""
    v = _visita(inspecao.id, auth_headers)
    h_cliente = await usuario_factory("cliente")
    r = getattr(client, metodo)(rota.format(v=v["id"]), json=corpo, headers=h_cliente)
    assert r.status_code == 403, r.text


def test_lacuna_14_sem_token_nao_escreve_em_visitas(auth_headers, inspecao):
    """Segurança: PUT sem Authorization deve dar 401. (Pode passar hoje; trava regressão.)"""
    v = _visita(inspecao.id, auth_headers)
    r = client.put(f"/api/v1/visitas/{v['id']}", json={"data": "2026-07-01", "servicos_executados": "x"})
    assert r.status_code == 401, r.text


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,  # só a asserção 403 pode "falhar esperado"; erro de infraestrutura falha de verdade
    reason="Pendente de decisão do dono: vínculo usuário<->contrato de DEC-27 (L15). Não resolvido "
    "em T21; quando a regra existir, remover o xfail (strict avisa se passar a funcionar).",
)
async def test_lacuna_15_auxiliar_nao_edita_visita_de_outro_autor(auth_headers, usuario_factory, inspecao):
    """DEC-27: auxiliar edita visitas 'dos contratos em que atua'. Não há vínculo usuário<->contrato no
    modelo; qualquer auxiliar edita visita criada pelo auditor. Esperado 403 para visita alheia."""
    v = _visita(inspecao.id, auth_headers)
    h_aux = await usuario_factory("auxiliar")
    r = client.put(
        f"/api/v1/visitas/{v['id']}",
        json={"data": "2026-07-01", "servicos_executados": "alterado pelo auxiliar"},
        headers=h_aux,
    )
    assert r.status_code == 403, r.text


# ---------------------------------------------------------------- PUT / imutáveis

def test_lacuna_16_put_nao_pode_receber_campos_imutaveis(auth_headers, inspecao):
    """RN-01/RN-18: `seq_numero`, `inspecao_id` e `criado_por_id` são imutáveis. Hoje o schema ignora
    campos extras em silêncio (200); o correto é rejeitar o payload (422, extra='forbid')."""
    v = _visita(inspecao.id, auth_headers)
    r = client.put(
        f"/api/v1/visitas/{v['id']}",
        json={
            "data": "2026-07-01",
            "servicos_executados": "x",
            "seq_numero": 99,
            "inspecao_id": str(uuid.uuid4()),
            "criado_por_id": str(uuid.uuid4()),
        },
        headers=auth_headers,
    )
    assert r.status_code == 422, r.text


def test_lacuna_17_put_sem_observacoes_nao_apaga_observacoes_existentes(auth_headers, inspecao):
    """RN-02: PUT sem o campo opcional `observacoes` zera o valor guardado (perda silenciosa de dado).
    Esperado: campo omitido preserva o valor (ou o contrato exige o campo)."""
    v = _visita(inspecao.id, auth_headers)
    client.put(
        f"/api/v1/visitas/{v['id']}",
        json={"data": "2026-07-01", "servicos_executados": "x", "observacoes": "Chuva forte"},
        headers=auth_headers,
    )
    r = client.put(
        f"/api/v1/visitas/{v['id']}",
        json={"data": "2026-07-01", "servicos_executados": "y"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["observacoes"] == "Chuva forte"


# ---------------------------------------------------------------- CRUD incompleto (RF-03)

def test_lacuna_18_visita_consultavel_e_equipe_corrigivel(auth_headers, inspecao):
    """RF-03: o registro de campo precisa ser corrigível. Hoje não há `GET /visitas/{id}` nem
    DELETE/PUT de mão de obra e medições (erro de digitação é irrecuperável). Esperado: GET 200 e
    DELETE de um item de mão de obra 204."""
    v = _visita(inspecao.id, auth_headers)
    mo = client.post(
        f"/api/v1/visitas/{v['id']}/mao-obra",
        json={"funcao": "Pedreiro", "quantidade": 3},
        headers=auth_headers,
    ).json()
    assert client.get(f"/api/v1/visitas/{v['id']}", headers=auth_headers).status_code == 200
    r = client.delete(f"/api/v1/visitas/{v['id']}/mao-obra/{mo['id']}", headers=auth_headers)
    assert r.status_code == 204, r.text


# ---------------------------------------------------------------- Cobertura das correções (T21, DEC-38)

def test_correcao_put_parcial_null_limpa_observacoes_e_rejeita_obrigatorios(auth_headers, inspecao):
    """DEC-38 (D): `observacoes: null` explícito limpa; `data`/`servicos_executados` null -> 422;
    PUT só com `observacoes` preserva data e serviços."""
    v = _visita(inspecao.id, auth_headers)
    url = f"/api/v1/visitas/{v['id']}"
    r = client.put(url, json={"observacoes": "Chuva"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert (corpo["observacoes"], corpo["servicos_executados"], corpo["data"]) == ("Chuva", "Fundação", "2026-07-01")
    r = client.put(url, json={"observacoes": None}, headers=auth_headers)
    assert r.status_code == 200 and r.json()["observacoes"] is None, r.text
    for invalido in ({"data": None}, {"servicos_executados": None}, {"servicos_executados": "  "}):
        assert client.put(url, json=invalido, headers=auth_headers).status_code == 422, invalido
    # a mesma data da própria visita não conflita consigo mesma
    assert client.put(url, json={"data": "2026-07-01"}, headers=auth_headers).status_code == 200


def test_correcao_crud_itens_mao_obra_e_medicao(auth_headers, inspecao):
    """DEC-38 (E): GET/PUT/DELETE de mão de obra e medição; item de outra visita -> 404."""
    v = _visita(inspecao.id, auth_headers, "2026-07-01")
    outra = _visita(inspecao.id, auth_headers, "2026-07-02")
    base = f"/api/v1/visitas/{v['id']}"
    base_outra = f"/api/v1/visitas/{outra['id']}"

    assert client.get(f"/api/v1/visitas/{uuid.uuid4()}", headers=auth_headers).status_code == 404

    mo = client.post(f"{base}/mao-obra", json={"funcao": " Pedreiro ", "quantidade": 3}, headers=auth_headers)
    assert mo.status_code == 201 and mo.json()["funcao"] == "Pedreiro", mo.text
    mo_id = mo.json()["id"]
    assert [i["id"] for i in client.get(f"{base}/mao-obra", headers=auth_headers).json()] == [mo_id]
    r = client.put(f"{base}/mao-obra/{mo_id}", json={"funcao": "Servente", "quantidade": 4}, headers=auth_headers)
    assert r.status_code == 200 and r.json()["quantidade"] == 4, r.text
    assert client.get(f"{base}/mao-obra/{mo_id}", headers=auth_headers).json()["funcao"] == "Servente"
    r = client.put(f"{base}/mao-obra/{mo_id}", json={"funcao": "Servente", "quantidade": 0}, headers=auth_headers)
    assert r.status_code == 422
    assert client.get(f"{base_outra}/mao-obra/{mo_id}", headers=auth_headers).status_code == 404
    assert client.delete(f"{base_outra}/mao-obra/{mo_id}", headers=auth_headers).status_code == 404

    med = client.post(
        f"{base}/medicoes", json={"descricao": "Concreto", "quantidade": 0, "unidade": "m3"}, headers=auth_headers
    )
    assert med.status_code == 201, med.text  # quantidade 0 é válida (>= 0)
    med_id = med.json()["id"]
    r = client.put(
        f"{base}/medicoes/{med_id}",
        json={"descricao": "Concreto", "quantidade": 12.5, "unidade": " m³ "},
        headers=auth_headers,
    )
    assert r.status_code == 200 and r.json()["unidade"] == "m³", r.text
    assert client.get(f"{base}/medicoes", headers=auth_headers).json()[0]["quantidade"] == 12.5
    r = client.put(
        f"{base}/medicoes/{med_id}",
        json={"descricao": "x", "quantidade": 1, "unidade": "un", "visita_id": outra["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 422  # extra='forbid': o item não troca de visita pelo payload

    assert client.delete(f"{base}/mao-obra/{mo_id}", headers=auth_headers).status_code == 204
    assert client.delete(f"{base}/medicoes/{med_id}", headers=auth_headers).status_code == 204
    assert client.get(f"{base}/mao-obra/{mo_id}", headers=auth_headers).status_code == 404
    detalhe = client.get(base, headers=auth_headers).json()
    assert detalhe["mao_obra"] == [] and detalhe["medicoes"] == []


async def test_correcao_rbac_endpoints_novos(auth_headers, usuario_factory, inspecao):
    """BL-42/RN-18: auxiliar lê e corrige itens de campo; cliente recebe 403 nos endpoints novos."""
    v = _visita(inspecao.id, auth_headers)
    base = f"/api/v1/visitas/{v['id']}"
    mo_id = client.post(
        f"{base}/mao-obra", json={"funcao": "Pedreiro", "quantidade": 1}, headers=auth_headers
    ).json()["id"]

    h_cliente = await usuario_factory("cliente")
    assert client.get(base, headers=h_cliente).status_code == 403
    assert client.get(f"{base}/medicoes", headers=h_cliente).status_code == 403
    assert client.delete(f"{base}/mao-obra/{mo_id}", headers=h_cliente).status_code == 403

    h_aux = await usuario_factory("auxiliar")
    assert client.get(base, headers=h_aux).status_code == 200
    r = client.put(f"{base}/mao-obra/{mo_id}", json={"funcao": "Pedreiro", "quantidade": 2}, headers=h_aux)
    assert r.status_code == 200, r.text
    assert client.delete(f"{base}/mao-obra/{mo_id}", headers=h_aux).status_code == 204
