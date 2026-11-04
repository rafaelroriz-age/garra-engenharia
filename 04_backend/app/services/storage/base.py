"""Interface `StorageClient` (Adapter Pattern, `00_docs/arquitetura.md` Seção 9.9).

Os serviços consumidores (ex.: upload de fotos de Visitas/Ocorrências, BL-11;
geração de PDF/DOCX, BL-12/BL-13) devem depender apenas desta interface — nunca
diretamente de `boto3` — para permitir trocar o provedor de armazenamento
(MinIO -> AWS S3 -> outro compatível com S3) sem alterar quem a consome.
"""
from abc import ABC, abstractmethod


class StorageClient(ABC):
    """Interface de armazenamento de objetos (arquivos binários)."""

    @abstractmethod
    def upload(
        self, key: str, file_bytes: bytes, content_type: str, *, max_size_bytes: int | None = None
    ) -> str:
        """Envia `file_bytes` para o armazenamento sob a chave `key`.

        Retorna a própria `key` (útil para encadear com o restante do fluxo).
        Lança `ValueError` se `key` for vazia, `file_bytes` for vazio, ou o
        tamanho exceder `max_size_bytes` (default: o limite defensivo de foto
        de `MAX_UPLOAD_SIZE_BYTES`). Artefatos maiores por natureza — como o
        PDF/DOCX final de um relatório, BL-12/BL-13/BL-22 — devem passar um
        `max_size_bytes` maior explicitamente; nunca desabilitar o limite.
        """

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Retorna o conteúdo binário do objeto `key`.

        Lança `ValueError` se `key` for vazia, ou `ObjectNotFoundError` se o
        objeto não existir no bucket.
        """

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Indica se o objeto `key` existe no armazenamento (sem baixá-lo).

        Lança `ValueError` se `key` for vazia.
        """

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove o objeto `key` do armazenamento (idempotente: não lança erro
        se o objeto já não existir — mesma semântica de `DELETE` da API S3).

        Lança `ValueError` se `key` for vazia.
        """

    @abstractmethod
    def generate_presigned_url(self, key: str, expires_in: int) -> str:
        """Gera uma URL pré-assinada de download (GET) para `key`, válida por
        `expires_in` segundos (RNF-07, ADR-02, Seção 10.1 A02 — nunca expor
        URLs públicas permanentes).

        Lança `ValueError` se `key` for vazia ou `expires_in` não for positivo.
        """
