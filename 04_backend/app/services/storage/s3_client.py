"""`S3StorageClient` — implementação `boto3` de `StorageClient` (BL-07).

Compatível com MinIO (dev/self-hosted, ver `05_infra/docker-compose.yml`) e
AWS S3 (produção, se adotado) — basta trocar as variáveis de ambiente
`MINIO_*` (DEC-02, ADR-02 em `00_docs/arquitetura.md`).
"""
import logging
from datetime import datetime
from functools import lru_cache

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import Settings, get_settings
from app.services.storage.base import StorageClient

logger = logging.getLogger(__name__)

# RNF-07 / ADR-02 / Seção 10.1 (A02): nunca expor URLs públicas permanentes —
# URLs de download são sempre pré-assinadas com expiração curta.
DEFAULT_PRESIGNED_URL_EXPIRES_IN_SECONDS = 15 * 60  # 15 minutos

# Limite defensivo de tamanho por arquivo (fotos de inspeção). Não há um RNF
# específico definindo o valor exato; 25 MB é generoso para fotos de câmera
# de celular e evita uploads acidentalmente enormes consumindo o bucket.
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024

_NOT_FOUND_ERROR_CODES = {"404", "NoSuchKey", "NoSuchBucket"}


class StorageError(Exception):
    """Erro genérico de operação de armazenamento."""


class ObjectNotFoundError(StorageError):
    """Objeto não encontrado no bucket."""


class S3StorageClient(StorageClient):
    """Cliente de armazenamento de objetos via `boto3`, compatível com S3/MinIO."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._bucket = self._settings.minio_bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=self._settings.minio_endpoint_url,
            aws_access_key_id=self._settings.minio_root_user,
            aws_secret_access_key=self._settings.minio_root_password,
            region_name="us-east-1",
            # SigV4 + path-style é o que o MinIO espera por padrão.
            config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Cria o bucket configurado se ele ainda não existir (idempotente)."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code not in _NOT_FOUND_ERROR_CODES:
                raise
            logger.info("Bucket '%s' não encontrado; criando...", self._bucket)
            self._client.create_bucket(Bucket=self._bucket)

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key or not key.strip():
            raise ValueError("A chave (key) do objeto não pode ser vazia.")

    def upload(
        self, key: str, file_bytes: bytes, content_type: str, *, max_size_bytes: int | None = None
    ) -> str:
        self._validate_key(key)
        if not file_bytes:
            raise ValueError("O conteúdo do arquivo não pode ser vazio.")
        limite = max_size_bytes if max_size_bytes is not None else MAX_UPLOAD_SIZE_BYTES
        if len(file_bytes) > limite:
            raise ValueError(
                f"Arquivo de {len(file_bytes)} bytes excede o limite máximo de "
                f"{limite} bytes por objeto."
            )

        self._client.put_object(Bucket=self._bucket, Key=key, Body=file_bytes, ContentType=content_type)
        return key

    def download(self, key: str) -> bytes:
        self._validate_key(key)
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in _NOT_FOUND_ERROR_CODES:
                raise ObjectNotFoundError(f"Objeto '{key}' não encontrado no bucket '{self._bucket}'.") from exc
            raise
        return response["Body"].read()

    def exists(self, key: str) -> bool:
        self._validate_key(key)
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in _NOT_FOUND_ERROR_CODES:
                return False
            raise
        return True

    def delete(self, key: str) -> None:
        self._validate_key(key)
        # `delete_object` da API S3 é idempotente por natureza: não lança erro
        # se a chave já não existir (204 em ambos os casos).
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def list_keys(self, prefix: str = "") -> list[str]:
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            keys.extend(obj["Key"] for obj in page.get("Contents", []))
        return keys

    def list_objects(self, prefix: str = "") -> list[tuple[str, datetime]]:
        """Pares `(chave, LastModified)` dos objetos sob `prefix` (só leitura; DEC-44)."""
        objetos: list[tuple[str, datetime]] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            objetos.extend((obj["Key"], obj["LastModified"]) for obj in page.get("Contents", []))
        return objetos

    def generate_presigned_url(
        self, key: str, expires_in: int = DEFAULT_PRESIGNED_URL_EXPIRES_IN_SECONDS
    ) -> str:
        self._validate_key(key)
        if expires_in <= 0:
            raise ValueError("expires_in deve ser um número de segundos positivo.")

        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )


@lru_cache
def get_storage_client() -> StorageClient:
    """Dependency do FastAPI (`Depends(get_storage_client)`).

    Cacheada (uma instância reutilizada por processo, mesmo padrão de
    `get_settings`) para não recriar o cliente `boto3` — e não repetir a
    checagem de existência do bucket — a cada requisição. Em testes, substitua
    via `app.dependency_overrides[get_storage_client] = lambda: fake_client`.
    """
    return S3StorageClient()
