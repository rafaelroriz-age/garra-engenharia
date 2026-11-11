"""Validação de completude do contexto do RFO antes de emitir (DEC-47 item 2).

Unidade (sem banco) para `validar_contexto_rfo`; integração (PostgreSQL de
05_infra/docker-compose.yml, localhost:5433) para `POST /inspecoes/{id}/relatorios/rfo` → 422.
"""
import copy

import pytest
from sqlalchemy import func, select

from app.models import Contrato, Inspecao, Relatorio, Responsavel
from app.services.report_generator.rfo_contexto import CAMPOS_OBRIGATORIOS_RFO, validar_contexto_rfo
from tests.test_relatorios_rfo_api import _auth, _TestSessionLocal, _url, api, cenario  # noqa: F401

CONTEXTO_COMPLETO = {
    "contrato": {"numero": "CT-1", "objeto": "Reforma", "data_inicio": "05/01/2026", "prazo_dias": 60, "art_fiscalizacao": "ART-1"},
    "fiscal": {"nome": "Eng.", "crea": "123-GO"},
}
CAMINHOS = [f"{secao}.{campo}" for secao, campo in CAMPOS_OBRIGATORIOS_RFO]


def test_contexto_completo_nao_tem_faltantes():
    assert validar_contexto_rfo(CONTEXTO_COMPLETO) == []


@pytest.mark.parametrize("caminho", CAMINHOS)
def test_cada_campo_nulo_e_listado(caminho):
    secao, campo = caminho.split(".")
    contexto = copy.deepcopy(CONTEXTO_COMPLETO)
    contexto[secao][campo] = None
    assert validar_contexto_rfo(contexto) == [caminho]


@pytest.mark.parametrize("caminho", [c for c in CAMINHOS if c != "contrato.prazo_dias"])
@pytest.mark.parametrize("vazio", ["", "   "])
def test_texto_em_branco_conta_como_ausente(caminho, vazio):
    secao, campo = caminho.split(".")
    contexto = copy.deepcopy(CONTEXTO_COMPLETO)
    contexto[secao][campo] = vazio
    assert validar_contexto_rfo(contexto) == [caminho]


def test_prazo_zero_conta_como_preenchido():
    contexto = copy.deepcopy(CONTEXTO_COMPLETO)
    contexto["contrato"]["prazo_dias"] = 0
    assert validar_contexto_rfo(contexto) == []


def test_secao_ausente_lista_todos_em_ordem_estavel():
    assert validar_contexto_rfo({}) == CAMINHOS
    assert validar_contexto_rfo({"contrato": None, "fiscal": None}) == CAMINHOS


def test_lista_de_obrigatorios_cobre_o_pedido_da_dec_47():
    assert set(CAMINHOS) == {
        "fiscal.crea", "contrato.art_fiscalizacao", "contrato.objeto", "contrato.data_inicio", "contrato.prazo_dias",
    }


# --- endpoint (PostgreSQL) -------------------------------------------------------


async def _contar_relatorios(inspecao_id) -> int:
    async with _TestSessionLocal() as s:
        consulta = select(func.count()).select_from(Relatorio).where(Relatorio.inspecao_id == inspecao_id)
        return (await s.execute(consulta)).scalar_one()


async def _anular(inspecao_id, campos: list[str]) -> None:
    async with _TestSessionLocal() as s:
        insp = await s.get(Inspecao, inspecao_id)
        contrato = await s.get(Contrato, insp.contrato_id)
        for campo in campos:
            if campo == "fiscal.crea":
                (await s.get(Responsavel, contrato.fiscal_id)).crea = None
            else:
                setattr(contrato, campo.split(".")[1], None)
        await s.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "campos",
    [["contrato.objeto"], ["fiscal.crea", "contrato.prazo_dias", "contrato.art_fiscalizacao"]],
)
async def test_endpoint_422_sem_relatorio_nem_upload(api, cenario, campos):  # noqa: F811
    client, storage, renderizador = api
    rfo_id = cenario["rfo_id"]
    await _anular(rfo_id, campos)
    objetos_antes = dict(storage.objetos)

    response = client.post(_url(rfo_id), headers=_auth(cenario["usuarios"]["auditor"]))

    assert response.status_code == 422, response.text
    corpo = response.json()
    assert corpo["type"].endswith("/rfo-contexto-incompleto")
    assert sorted(e["field"] for e in corpo["errors"]) == sorted(campos)
    assert renderizador.chamadas == []
    assert storage.objetos == objetos_antes
    assert await _contar_relatorios(rfo_id) == 0


def test_endpoint_contrato_completo_emite_201(api, cenario):  # noqa: F811
    client, _storage, _ = api
    response = client.post(_url(cenario["rfo_id"]), headers=_auth(cenario["usuarios"]["auditor"]))
    assert response.status_code == 201, response.text
