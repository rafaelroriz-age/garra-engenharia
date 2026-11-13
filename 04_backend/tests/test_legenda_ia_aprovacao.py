# ruff: noqa: F811, F401
"""Aprovação da legenda por IA só pelo auditor e invalidação ao editar/regerar (DEC-42 A e B).

Reaproveita as fixtures de `test_legenda_ia_endpoints.py`. Requer PostgreSQL e MinIO.
"""
from tests.test_legenda_ia_endpoints import (  # fixtures e helpers reaproveitados
    _gerar,
    _nova_foto,
    _put,
    criar_foto,
    fake_ia,
    nome_prompt,
    prompt_ativo,
    usuarios,
    vinculos,
)


def _foto_aprovada(usuarios, criar_foto):
    foto_id = _nova_foto(criar_foto)
    _gerar(foto_id, usuarios["auditor"], {"legenda_bruta": "fissura"})
    resposta = _put(foto_id, usuarios["auditor"], {"aprovar_legenda_ia": True})
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["status_validacao_ia"] == "aprovada"
    return foto_id


def test_auxiliar_aprovar_retorna_403_rfc7807(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)
    _gerar(foto_id, usuarios["auxiliar"], {"legenda_bruta": "fissura"})

    resposta = _put(foto_id, usuarios["auxiliar"], {"aprovar_legenda_ia": True})

    assert resposta.status_code == 403
    assert resposta.headers["content-type"].startswith("application/problem+json")
    assert resposta.json()["type"].endswith("/acesso-negado")


def test_auxiliar_gera_e_edita_rascunho(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _nova_foto(criar_foto)

    gerada = _gerar(foto_id, usuarios["auxiliar"], {"legenda_bruta": "fissura"})
    editada = _put(foto_id, usuarios["auxiliar"], {"legenda": "Fissura no pilar", "ordem": 3})

    assert gerada.status_code == 200 and gerada.json()["status_validacao_ia"] == "rascunho"
    assert editada.status_code == 200, editada.text
    assert editada.json()["legenda"] == "Fissura no pilar"
    assert editada.json()["aprovado_por_id"] is None


def test_auditor_aprova(usuarios, prompt_ativo, fake_ia, criar_foto):
    assert _foto_aprovada(usuarios, criar_foto)


def test_regerar_legenda_aprovada_invalida_aprovacao(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _foto_aprovada(usuarios, criar_foto)

    corpo = _gerar(foto_id, usuarios["auxiliar"]).json()

    assert corpo["status_validacao_ia"] == "rascunho"
    assert corpo["aprovado_por_id"] is None and corpo["aprovado_em"] is None


def test_put_que_muda_legenda_aprovada_invalida(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _foto_aprovada(usuarios, criar_foto)

    resposta = _put(foto_id, usuarios["auxiliar"], {"legenda": "Outro texto"})

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["legenda"] == "Outro texto"
    assert corpo["status_validacao_ia"] == "rascunho"
    assert corpo["aprovado_por_id"] is None and corpo["aprovado_em"] is None


def test_put_sem_mudar_legenda_nao_invalida(usuarios, prompt_ativo, fake_ia, criar_foto):
    foto_id = _foto_aprovada(usuarios, criar_foto)

    so_ordem = _put(foto_id, usuarios["auxiliar"], {"ordem": 5})
    mesma = _put(foto_id, usuarios["auxiliar"], {"legenda": so_ordem.json()["legenda"]})

    for resposta in (so_ordem, mesma):
        assert resposta.status_code == 200, resposta.text
        assert resposta.json()["status_validacao_ia"] == "aprovada"
        assert resposta.json()["aprovado_por_id"] == str(usuarios["auditor"])
