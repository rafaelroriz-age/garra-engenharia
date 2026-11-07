"""Enum fechado de `origem` no payload de vínculo de foto (DEC-43).

- Testes de schema: Pydantic puro, sem banco.
- Teste de endpoint: `POST` de vínculo com `origem` inválida deve retornar 422.
  Precisa do PostgreSQL de 05_infra (localhost:5433) para autenticar; sem ele, é pulado.
"""

import socket
import uuid

import pytest
from app.schemas.foto import FotoRead, FotoVincularPayload
from pydantic import ValidationError

from tests.test_fotos import auth_headers, client  # noqa: F401  (fixture e cliente de teste)

VALORES_VALIDOS = ["upload_manual", "lightshot", "clipboard"]
VALORES_INVALIDOS = ["upload", "camera", "", "UPLOAD_MANUAL", "Lightshot", "desconhecida"]


def _postgres_no_ar(host: str = "localhost", porta: int = 5433) -> bool:
    try:
        with socket.create_connection((host, porta), timeout=1):
            return True
    except OSError:
        return False


@pytest.mark.parametrize("origem", VALORES_VALIDOS)
def test_payload_aceita_origem_do_enum(origem):
    payload = FotoVincularPayload(storage_key="fotos/x.jpg", origem=origem)
    assert payload.origem == origem


@pytest.mark.parametrize("origem", VALORES_INVALIDOS)
def test_payload_rejeita_origem_fora_do_enum(origem):
    with pytest.raises(ValidationError):
        FotoVincularPayload(storage_key="fotos/x.jpg", origem=origem)


def test_payload_exige_origem():
    with pytest.raises(ValidationError):
        FotoVincularPayload(storage_key="fotos/x.jpg")


def test_payload_rejeita_origem_nula():
    with pytest.raises(ValidationError):
        FotoVincularPayload(storage_key="fotos/x.jpg", origem=None)


def test_leitura_aceita_origem_antiga_gravada():
    """Registros antigos (ex.: 'upload') continuam legíveis: o enum vale só para entrada."""
    leitura = FotoRead(
        id=uuid.uuid4(),
        created_at="2026-09-10T12:00:00",
        storage_key="fotos/antiga.jpg",
        origem="upload",
    )
    assert leitura.origem == "upload"


@pytest.mark.skipif(
    not _postgres_no_ar(),
    reason="PostgreSQL de 05_infra indisponível em localhost:5433; teste de endpoint não rodou",
)
@pytest.mark.parametrize("origem", ["upload", "camera"])
def test_endpoint_vincular_com_origem_invalida_retorna_422(auth_headers, origem):  # noqa: F811
    response = client.post(
        f"/api/v1/ocorrencias/{uuid.uuid4()}/fotos",
        json={"storage_key": "fotos/x.jpg", "origem": origem},
        headers=auth_headers,
    )
    assert response.status_code == 422
