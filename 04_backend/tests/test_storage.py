"""Testes de integração do `StorageClient` (BL-07) contra o MinIO real de
`05_infra/docker-compose.yml`.

Requer o serviço `minio` rodando (`cd 05_infra && docker compose up -d minio`)
e as variáveis `MINIO_*` configuradas em `04_backend/.env` (ver `.env.example`),
apontando para o MinIO publicado em `localhost` — mesmo padrão de
`tests/test_models.py`/`tests/test_gabarito.py` para o PostgreSQL.
"""
import uuid

import httpx
import pytest
from app.services.storage.s3_client import (
    MAX_UPLOAD_SIZE_BYTES,
    ObjectNotFoundError,
    S3StorageClient,
)


@pytest.fixture(scope="module")
def storage_client() -> S3StorageClient:
    """Cliente único por módulo de teste (cria/valida o bucket uma vez)."""
    return S3StorageClient()


@pytest.fixture
def object_key() -> str:
    """Chave isolada por teste, sob um prefixo dedicado para não colidir com
    dados reais e facilitar limpeza manual se algum teste falhar antes do
    `delete` de teardown."""
    return f"tests/bl-07/{uuid.uuid4()}.txt"


def test_upload_and_download_roundtrip(storage_client: S3StorageClient, object_key: str):
    """Upload seguido de download deve retornar exatamente o mesmo conteúdo."""
    content = b"conteudo de teste BL-07"

    returned_key = storage_client.upload(object_key, content, content_type="text/plain")
    downloaded = storage_client.download(object_key)

    assert returned_key == object_key
    assert downloaded == content

    storage_client.delete(object_key)


def test_download_raises_object_not_found_for_missing_key(storage_client: S3StorageClient):
    """Download de uma chave inexistente deve lançar `ObjectNotFoundError`."""
    missing_key = f"tests/bl-07/inexistente-{uuid.uuid4()}.txt"

    with pytest.raises(ObjectNotFoundError):
        storage_client.download(missing_key)


def test_delete_is_idempotent(storage_client: S3StorageClient, object_key: str):
    """Deletar duas vezes a mesma chave não deve lançar erro (semântica S3)."""
    storage_client.upload(object_key, b"conteudo", content_type="text/plain")

    storage_client.delete(object_key)
    storage_client.delete(object_key)  # segunda chamada: não deve lançar


def test_generate_presigned_url_allows_anonymous_download(storage_client: S3StorageClient, object_key: str):
    """A URL pré-assinada deve permitir download via HTTP puro, sem credenciais."""
    content = b"conteudo acessivel via url pre-assinada"
    storage_client.upload(object_key, content, content_type="text/plain")

    url = storage_client.generate_presigned_url(object_key, expires_in=60)

    assert url.startswith("http")
    assert "X-Amz-Expires=60" in url

    response = httpx.get(url)

    assert response.status_code == 200
    assert response.content == content

    storage_client.delete(object_key)


def test_generate_presigned_url_rejects_empty_key(storage_client: S3StorageClient):
    with pytest.raises(ValueError):
        storage_client.generate_presigned_url("", expires_in=60)


def test_generate_presigned_url_rejects_non_positive_expiration(storage_client: S3StorageClient, object_key: str):
    with pytest.raises(ValueError):
        storage_client.generate_presigned_url(object_key, expires_in=0)


def test_upload_rejects_empty_key(storage_client: S3StorageClient):
    with pytest.raises(ValueError):
        storage_client.upload("", b"conteudo", content_type="text/plain")


def test_upload_rejects_empty_content(storage_client: S3StorageClient):
    with pytest.raises(ValueError):
        storage_client.upload("tests/bl-07/vazio.txt", b"", content_type="text/plain")


def test_upload_rejects_file_exceeding_max_size(storage_client: S3StorageClient):
    oversized_content = b"0" * (MAX_UPLOAD_SIZE_BYTES + 1)

    with pytest.raises(ValueError):
        storage_client.upload("tests/bl-07/muito-grande.bin", oversized_content, content_type="application/octet-stream")
