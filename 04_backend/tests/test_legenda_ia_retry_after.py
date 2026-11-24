"""Retry-After no header do 429 da legenda por IA (pendência da T35).

Reaproveita a fixture `rota` de `test_legenda_ia_limites.py` (rota real, banco/storage falsos,
relógio falso) e confere que o header acompanha o corpo RFC 7807 sem alterá-lo.
"""
import uuid

from tests.test_legenda_ia_limites import rota  # noqa: F401  (fixture reutilizada)


def _estourar(rota):  # noqa: F811
    foto_id = rota.nova_foto()
    respostas = [rota.gerar(foto_id) for _ in range(3)]
    assert [r.status_code for r in respostas] == [200, 200, 429]
    return respostas[-1]


def test_429_traz_retry_after_inteiro_igual_ao_corpo(rota):  # noqa: F811
    resposta = _estourar(rota)

    header = resposta.headers["retry-after"]
    assert header.isdigit() and int(header) >= 1
    corpo = resposta.json()
    assert corpo["errors"] == [{"field": "retry_after_segundos", "message": header}]
    assert corpo["status"] == 429
    assert resposta.headers["content-type"].startswith("application/problem+json")


def test_erros_comuns_nao_tem_retry_after(rota):  # noqa: F811
    inexistente = rota.gerar(uuid.uuid4())
    assert inexistente.status_code == 404
    assert "retry-after" not in inexistente.headers

    invalido = rota.gerar("nao-e-uuid")
    assert invalido.status_code == 422
    assert "retry-after" not in invalido.headers
