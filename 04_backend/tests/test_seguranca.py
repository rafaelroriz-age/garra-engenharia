"""Testes da revisão de segurança OWASP (BL-23, RNF-05).

Cobre os controles adicionados nesta tarefa: limite de tentativas de login
(A07), cabeçalhos de segurança e correlação por `X-Request-ID` (A05/A09),
registro protegido (A01) e fail-closed de configuração de produção (A05).
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core import rate_limit
from app.core.config import Settings
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _limpar_rate_limit():
    rate_limit.resetar()
    yield
    rate_limit.resetar()


def test_login_bloqueia_apos_tentativas_malsucedidas_consecutivas():
    email = f"forca-bruta-{uuid.uuid4()}@garra-engenharia.com.br"
    payload = {"email": email, "senha": "senha-errada-123"}

    for _ in range(rate_limit.MAX_TENTATIVAS):
        assert client.post("/api/v1/auth/login", json=payload).status_code == 401

    bloqueado = client.post("/api/v1/auth/login", json=payload)

    assert bloqueado.status_code == 429
    assert int(bloqueado.headers["Retry-After"]) > 0


def test_login_bem_sucedido_zera_o_contador_de_falhas():
    rate_limit.registrar_falha("testclient", "alguem@garra.com")
    rate_limit.registrar_sucesso("testclient", "alguem@garra.com")

    assert rate_limit.segundos_ate_liberar("testclient", "alguem@garra.com") == 0


def test_respostas_incluem_cabecalhos_de_seguranca_e_request_id():
    response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert uuid.UUID(response.headers["X-Request-ID"])


def test_request_id_enviado_pelo_cliente_e_ecoado_para_correlacao():
    request_id = str(uuid.uuid4())

    response = client.get("/health", headers={"X-Request-ID": request_id})

    assert response.headers["X-Request-ID"] == request_id


def test_registro_publico_bloqueado_quando_ja_existem_usuarios():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Anônimo",
            "email": f"anonimo-{uuid.uuid4()}@garra-engenharia.com.br",
            "senha": "senha-forte-123",
        },
    )

    assert response.status_code == 403


def test_settings_recusa_jwt_secret_default_em_producao():
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings(environment="production", jwt_secret_key="changeme", _env_file=None)


def test_settings_recusa_cors_wildcard_em_producao():
    with pytest.raises(ValueError, match="BACKEND_CORS_ORIGINS"):
        Settings(
            environment="production",
            jwt_secret_key="x" * 40,
            backend_cors_origins="*",
            _env_file=None,
        )


def test_settings_aceita_configuracao_valida_de_producao():
    settings = Settings(
        environment="production",
        jwt_secret_key="x" * 40,
        backend_cors_origins="https://app.garra-engenharia.com.br",
        _env_file=None,
    )

    assert settings.is_development is False
