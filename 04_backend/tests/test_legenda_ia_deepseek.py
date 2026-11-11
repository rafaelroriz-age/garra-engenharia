"""Cliente DeepSeek de legenda por IA (V1-07): sem rede, via httpx.MockTransport."""
import asyncio
import base64
import io
import json

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from app.core.errors import DomainError
from app.services.legenda_ia import (
    DeepSeekLegendaIAClient,
    FakeLegendaIAClient,
    obter_cliente_provedor,
)
from app.services.legenda_ia.deepseek import ProvedorIAIndisponivel, reduzir_imagem_para_data_uri
from app.services.legenda_ia.saneamento import SaidaLegendaIAInvalida

CHAVE = "sk-teste-nao-logar"


def _jpeg(lado: int = 2000) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (lado, lado // 2), (10, 120, 200)).save(buf, format="JPEG")
    return buf.getvalue()


def _resposta(conteudo: str) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": conteudo}}]}


def _cliente(handler, **kw) -> DeepSeekLegendaIAClient:
    return DeepSeekLegendaIAClient(CHAVE, transport=httpx.MockTransport(handler), **kw)


def _gerar(cliente: DeepSeekLegendaIAClient, bruta: str | None = "fissura na parede"):
    return asyncio.run(cliente.gerar_legenda(_jpeg(), "PROMPT", bruta))


def test_resposta_valida_vira_resultado_e_requisicao_correta():
    vistos: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        vistos.append(req)
        return httpx.Response(
            200,
            json=_resposta(
                json.dumps({"legenda_sugerida": "Fissura vertical.", "alertas": ["a"], "pendencias": []})
            ),
        )

    r = _gerar(_cliente(handler, modelo="m-x"))

    assert (r.legenda_sugerida, r.alertas, r.pendencias, r.modo) == ("Fissura vertical.", ["a"], [], "texto")
    req = vistos[0]
    assert str(req.url) == "https://api.deepseek.com/chat/completions"
    assert req.headers["authorization"] == f"Bearer {CHAVE}"
    corpo = json.loads(req.content)
    assert corpo["model"] == "m-x"
    assert corpo["response_format"] == {"type": "json_object"}
    assert corpo["messages"][0]["role"] == "system" and "PROMPT" in corpo["messages"][0]["content"]
    assert corpo["messages"][1] == {"role": "user", "content": "fissura na parede"}


def test_modo_texto_nao_envia_imagem():
    corpos: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        corpos.append(req.content.decode())
        return httpx.Response(200, json=_resposta('{"legenda_sugerida": "ok"}'))

    _gerar(_cliente(handler))

    assert "image_url" not in corpos[0] and "base64" not in corpos[0]


def test_modo_imagem_envia_data_uri_jpeg_reduzido():
    corpos: list[dict] = []

    def handler(req: httpx.Request) -> httpx.Response:
        corpos.append(json.loads(req.content))
        return httpx.Response(200, json=_resposta('{"legenda_sugerida": "ok"}'))

    r = _gerar(_cliente(handler, enviar_imagem=True))

    assert r.modo == "imagem"
    partes = corpos[0]["messages"][1]["content"]
    url = next(p["image_url"]["url"] for p in partes if p["type"] == "image_url")
    assert url.startswith("data:image/jpeg;base64,")
    img = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert max(img.size) <= 1024
    assert {"type": "text", "text": "fissura na parede"} in partes


def test_reducao_nao_amplia_imagem_pequena():
    url = reduzir_imagem_para_data_uri(_jpeg(200))
    img = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert img.size == (200, 100)


@pytest.mark.parametrize(
    "conteudo",
    ["isto não é json", "", "[1, 2]", '{"alertas": []}', '{"legenda_sugerida": "  "}',
     '{"legenda_sugerida": "x", "alertas": "texto"}', '{"legenda_sugerida": 5}'],
)
def test_json_invalido_vira_erro_de_dominio(conteudo):
    cliente = _cliente(lambda req: httpx.Response(200, json=_resposta(conteudo)))
    with pytest.raises(SaidaLegendaIAInvalida):
        _gerar(cliente)


def test_corpo_http_fora_do_formato_vira_erro_de_dominio():
    cliente = _cliente(lambda req: httpx.Response(200, json={"choices": []}))
    with pytest.raises(SaidaLegendaIAInvalida):
        _gerar(cliente)


@pytest.mark.parametrize("status", [401, 429, 500])
def test_http_de_erro_vira_erro_tratado_sem_vazar_chave(status):
    cliente = _cliente(lambda req: httpx.Response(status, text=f"detalhe {CHAVE}"))
    with pytest.raises(ProvedorIAIndisponivel) as exc:
        _gerar(cliente)
    assert exc.value.status_code == 502
    assert str(status) in str(exc.value) and CHAVE not in str(exc.value)


def test_timeout_vira_erro_tratado():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("lento", request=req)

    with pytest.raises(ProvedorIAIndisponivel, match="tempo esgotado"):
        _gerar(_cliente(handler))


def test_falha_de_rede_vira_erro_tratado():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sem rota", request=req)

    with pytest.raises(ProvedorIAIndisponivel, match="rede"):
        _gerar(_cliente(handler))


def test_log_nao_contem_chave_nem_imagem(caplog):
    caplog.set_level("DEBUG")
    cliente = _cliente(lambda req: httpx.Response(500, text="x"), enviar_imagem=True)
    with pytest.raises(ProvedorIAIndisponivel):
        _gerar(cliente)
    assert CHAVE not in caplog.text and "base64" not in caplog.text


# --- Seleção do provedor por configuração -------------------------------------------------


def _usar(monkeypatch, **campos) -> None:
    monkeypatch.setattr("app.services.legenda_ia.get_settings", lambda: Settings(**campos))


def test_padrao_e_fake_e_nao_exige_chave(monkeypatch):
    assert Settings().legenda_ia_provedor == "fake"
    _usar(monkeypatch)
    assert isinstance(obter_cliente_provedor(), FakeLegendaIAClient)


def test_deepseek_com_chave_devolve_adapter(monkeypatch):
    _usar(monkeypatch, legenda_ia_provedor="deepseek", deepseek_api_key=SecretStr(CHAVE))
    assert isinstance(obter_cliente_provedor(), DeepSeekLegendaIAClient)


def test_deepseek_sem_chave_em_desenvolvimento_responde_503(monkeypatch):
    _usar(monkeypatch, legenda_ia_provedor="deepseek")
    with pytest.raises(DomainError) as exc:
        obter_cliente_provedor()
    assert exc.value.status_code == 503


def test_fake_em_producao_responde_503(monkeypatch):
    _usar(monkeypatch, environment="production", jwt_secret_key="x" * 40)
    with pytest.raises(DomainError) as exc:
        obter_cliente_provedor()
    assert exc.value.status_code == 503


def test_producao_com_deepseek_sem_chave_falha_na_inicializacao():
    with pytest.raises(ValidationError, match="DEEPSEEK_API_KEY"):
        Settings(environment="production", jwt_secret_key="x" * 40, legenda_ia_provedor="deepseek")


def test_producao_com_deepseek_e_chave_sobe():
    s = Settings(
        environment="production",
        jwt_secret_key="x" * 40,
        legenda_ia_provedor="deepseek",
        deepseek_api_key=SecretStr(CHAVE),
    )
    assert CHAVE not in repr(s)
