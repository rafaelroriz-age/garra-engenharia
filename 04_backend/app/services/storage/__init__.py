"""Serviço de armazenamento de arquivos (fotos de inspeção) — BL-07.

Ver RNF-07 (`00_docs/estudo-do-contexto.md`), DEC-02
(`00_docs/projeto/decisoes.md`) e Adapter Pattern (`00_docs/arquitetura.md`
Seção 9.9): `StorageClient` é a interface consumida pelos serviços de domínio;
`S3StorageClient` é a única implementação concreta hoje (boto3, compatível com
MinIO e AWS S3), o que permite trocar de provedor sem alterar quem a consome.
"""
from app.services.storage.base import StorageClient
from app.services.storage.s3_client import (
    MAX_UPLOAD_SIZE_BYTES,
    ObjectNotFoundError,
    S3StorageClient,
    StorageError,
    get_storage_client,
)

__all__ = [
    "StorageClient",
    "S3StorageClient",
    "StorageError",
    "ObjectNotFoundError",
    "MAX_UPLOAD_SIZE_BYTES",
    "get_storage_client",
]
