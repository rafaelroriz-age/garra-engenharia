"""Revisão de segurança dos endpoints de legenda por IA, fotos e visitas (BL-23, 2ª passada).

Cobre o que entrou depois da revisão de 2026-08-07: `POST /fotos/{id}/legenda-ia/gerar`,
`PUT /fotos/{id}` com `aprovar_legenda_ia`, `DELETE /fotos/upload` e o CRUD de visitas.
Relatório: `00_docs/backlog-auto/seguranca-legenda-ia.md` (achados SEG-IA-xx).

- Testes sem marca verificam controles que JÁ funcionam (regressão).
- Testes `xfail(strict=True)` afirmam o comportamento CORRETO de uma lacuna demonstrada; quando
  a correção entrar, o `strict` faz a suíte falhar e a marca deve ser removida.

Requer PostgreSQL e MinIO de `05_infra/docker-compose.yml` (mesmos fixtures de
`test_legenda_ia_endpoints.py`).
"""
# ruff: noqa: F811  (fixtures importadas de test_legenda_ia_endpoints são reusadas como argumentos)
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.legenda_ia import LegendaIAResultado, get_legenda_ia_client
from app.services.storage import get_storage_client

# Reaproveita fixtures e helpers do arquivo de endpoints (banco, MinIO, usuários por papel).
from tests.test_legenda_ia_endpoints import (  # noqa: F401
    _gerar,
    _headers,
    _nova_foto,
    _put,
    criar_foto,
    fake_ia,
    nome_prompt,
    prompt_ativo,
    usuarios,
    vinculos,
)

client = TestClient(app)


class _ClienteLongo:
    """Cliente de IA que devolve uma sugestão muito maior que o limite da legenda (500)."""

    async def gerar_legenda(self, imagem, prompt, legenda_bruta=None):
        return LegendaIAResultado(legenda_sugerida="A" * 2000, alertas=["x"] * 500)


class _ClienteQuebrado:
    async def gerar_legenda(self, imagem, prompt, legenda_bruta=None):
        raise RuntimeError("401 invalid api key sk-SEGREDO-DO-PROVEDOR")


# --- Controles que funcionam (regressão) ------------------------------------------------------


def test_cliente_nao_acessa_visitas_nem_itens(usuarios):
    h = _headers(usuarios["cliente"])
    v, i = uuid.uuid4(), uuid.uuid4()
    chamadas = [
        ("get", f"/api/v1/visitas/{v}", None),
        ("put", f"/api/v1/visitas/{v}", {"observacoes": "x"}),
        ("get", f"/api/v1/visitas/{v}/mao-obra", None),
        ("post", f"/api/v1/visitas/{v}/mao-obra", {"funcao": "x", "quantidade": 1}),
        ("put", f"/api/v1/visitas/{v}/mao-obra/{i}", {"quantidade": 2}),
        ("delete", f"/api/v1/visitas/{v}/mao-obra/{i}", None),
        ("get", f"/api/v1/visitas/{v}/medicoes", None),
        ("post", f"/api/v1/visitas/{v}/medicoes", {"descricao": "x", "quantidade": 1, "unidade": "m"}),
        ("put", f"/api/v1/visitas/{v}/medicoes/{i}", {"quantidade": 2}),
        ("delete", f"/api/v1/visitas/{v}/medicoes/{i}", None),
        ("delete", "/api/v1/fotos/upload", {"storage_key": f"fotos/{uuid.uuid4()}.png"}),
        ("delete", f"/api/v1/fotos/{v}", None),
    ]
    app.dependency_overrides[get_storage_client] = lambda: object()  # sem MinIO: 403 vem antes do uso
    try:
        for metodo, url, corpo in chamadas:
            resp = client.request(metodo.upper(), url, headers=h, **({"json": corpo} if corpo is not None else {}))
            assert resp.status_code == 403, (metodo, url, resp.status_code)
    finally:
        app.dependency_overrides.pop(get_storage_client, None)


@pytest.mark.parametrize(
    "chave",
    [
        "../fotos/" + "0" * 8 + "-0000-0000-0000-" + "0" * 12 + ".png",
        "/etc/passwd",
        "fotos/../../outro-bucket/x.png",
        "outro/" + str(uuid.uuid4()) + ".png",
        "fotos/" + str(uuid.uuid4()) + ".png/../../x",
        "fotos/" + str(uuid.uuid4()) + ".svg",
        "fotos/" + str(uuid.uuid4()).upper() + ".png",
    ],
)
def test_descartar_upload_recusa_chave_fora_do_padrao(usuarios, chave):
    apagados = []

    class _StorageFalso:
        def delete(self, key):
            apagados.append(key)

    app.dependency_overrides[get_storage_client] = lambda: _StorageFalso()
    try:
        resp = client.request(
            "DELETE", "/api/v1/fotos/upload", json={"storage_key": chave}, headers=_headers(usuarios["auditor"])
        )
    finally:
        app.dependency_overrides.pop(get_storage_client, None)

    assert resp.status_code in (400, 422)
    assert apagados == []


def test_gerar_recusa_legenda_bruta_acima_do_limite(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)

    resp = _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "x" * 5001})

    assert resp.status_code == 422
    assert fake_ia.chamadas == 0


def test_erro_do_provedor_nao_vaza_detalhe_nem_grava_sugestao(usuarios, prompt_ativo, criar_foto):
    foto_id = _nova_foto(criar_foto)
    app.dependency_overrides[get_legenda_ia_client] = lambda: _ClienteQuebrado()
    try:
        seguro = TestClient(app, raise_server_exceptions=False)
        resp = seguro.post(
            f"/api/v1/fotos/{foto_id}/legenda-ia/gerar", json={}, headers=_headers(usuarios["auditor"])
        )
    finally:
        app.dependency_overrides.pop(get_legenda_ia_client, None)

    assert resp.status_code == 500
    assert "sk-SEGREDO" not in resp.text and "api key" not in resp.text.lower()
    atual = client.put(f"/api/v1/fotos/{foto_id}", json={}, headers=_headers(usuarios["auditor"])).json()
    assert atual["legenda_ia_sugerida"] is None and atual["status_validacao_ia"] is None


def test_erro_de_arquivo_ausente_nao_expoe_storage_key(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)
    chave = client.put(f"/api/v1/fotos/{foto_id}", json={}, headers=_headers(usuarios["auditor"])).json()[
        "storage_key"
    ]
    get_storage_client().delete(chave)

    resp = _gerar(foto_id, usuarios["auditor"], {})

    assert resp.status_code in (400, 404, 422)
    assert chave not in resp.text


# --- Lacunas demonstradas (xfail strict = comportamento correto ainda não implementado) --------


@pytest.mark.xfail(strict=True, reason="SEG-IA-01: sem limite de taxa/custo em /legenda-ia/gerar")
def test_gerar_tem_limite_de_taxa_por_usuario(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)

    codigos = [_gerar(foto_id, usuarios["auxiliar"], {"legenda_bruta": f"t{i}"}).status_code for i in range(40)]

    assert 429 in codigos, "40 gerações seguidas (40 chamadas pagas ao LLM) não foram limitadas"


@pytest.mark.xfail(strict=True, reason="SEG-IA-02: regerar mantém aprovador/data da aprovação anterior")
def test_regerar_apos_aprovar_limpa_aprovacao_anterior(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)
    _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "trinca"})
    assert _put(foto_id, usuarios["auditor"], {"aprovar_legenda_ia": True}).json()["status_validacao_ia"] == "aprovada"

    novo = _gerar(foto_id, usuarios["auxiliar"], {"legenda_bruta": "outra descrição"}).json()

    assert novo["status_validacao_ia"] == "rascunho"
    assert novo["aprovado_por_id"] is None and novo["aprovado_em"] is None  # RN-17


@pytest.mark.xfail(strict=True, reason="SEG-IA-03 (DEC-37 DP-10): editar legenda aprovada mantém o aprovador antigo")
def test_editar_legenda_aprovada_nao_atribui_edicao_ao_aprovador_anterior(
    usuarios, prompt_ativo, fake_ia, criar_foto
):
    foto_id = _nova_foto(criar_foto)
    _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "trinca"})
    _put(foto_id, usuarios["auditor"], {"aprovar_legenda_ia": True})

    resp = _put(foto_id, usuarios["auxiliar"], {"legenda": "texto alterado depois da aprovação"})

    corpo = resp.json()
    reprovada = resp.status_code == 422 or corpo["status_validacao_ia"] != "aprovada"
    reatribuida = resp.status_code == 200 and corpo["aprovado_por_id"] == str(usuarios["auxiliar"])
    assert reprovada or reatribuida


@pytest.mark.xfail(strict=True, reason="SEG-IA-04: sugestão do LLM acima de 500 caracteres burla o limite da legenda")
def test_sugestao_longa_do_llm_nao_burla_limite_da_legenda(usuarios, prompt_ativo, criar_foto):
    foto_id = _nova_foto(criar_foto)
    app.dependency_overrides[get_legenda_ia_client] = lambda: _ClienteLongo()
    try:
        gerada = _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "x"})
    finally:
        app.dependency_overrides.pop(get_legenda_ia_client, None)
    assert gerada.status_code in (200, 422, 502)

    aprovada = _put(foto_id, usuarios["auditor"], {"aprovar_legenda_ia": True})

    legenda = aprovada.json().get("legenda") if aprovada.status_code == 200 else None
    assert legenda is None or len(legenda) <= 500
    if gerada.status_code == 200:
        assert len(gerada.json()["alertas_ia"]) <= 50


@pytest.mark.xfail(
    strict=True,
    reason="SEG-IA-05 (decisão pendente): RN-16 exige aprovação do profissional responsável; hoje o auxiliar aprova",
)
def test_auxiliar_nao_aprova_legenda_ia(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)
    _gerar(foto_id, usuarios["auxiliar"], {"legenda_bruta": "trinca"})

    resp = _put(foto_id, usuarios["auxiliar"], {"aprovar_legenda_ia": True})

    assert resp.status_code == 403


@pytest.mark.xfail(strict=True, reason="SEG-IA-06: auxiliar remove foto já aprovada (sem trilha nem bloqueio)")
def test_auxiliar_nao_remove_foto_com_legenda_aprovada(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)
    _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "trinca"})
    _put(foto_id, usuarios["auditor"], {"aprovar_legenda_ia": True})

    resp = client.delete(f"/api/v1/fotos/{foto_id}", headers=_headers(usuarios["auxiliar"]))

    assert resp.status_code in (403, 409)
