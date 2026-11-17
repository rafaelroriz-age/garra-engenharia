"""`LocalStorageClient` — armazenamento em disco local (DEC-57, P6).

Com o backend no PC do dono não há MinIO/S3: os objetos vão para
`STORAGE_LOCAL_DIR` (fora do git). A "URL pré-assinada" é um token HMAC-SHA256
servido por `GET /api/v1/arquivos/{token}` (ver `app/api/v1/arquivos.py`).

Decisões:
- Content-type: inferido pela extensão da chave (`mimetypes` + mapa explícito),
  sem arquivo lateral. Todas as chaves do sistema têm extensão (fotos/*.jpg|png,
  relatórios .pdf|.docx); isso evita arquivos `.meta.json` poluindo listagens.
  Extensão desconhecida => `application/octet-stream`.
- Gravação atômica: arquivo temporário no mesmo diretório + `os.replace`.
- Path traversal: a chave resolvida tem de ficar dentro da raiz.
- URL absoluta: `PUBLIC_BASE_URL` se definida; senão a base do request corrente
  (X-Forwarded-Proto/Host do cloudflared, via `RequestBaseUrlMiddleware`);
  sem nenhuma das duas, URL relativa à API (`/api/v1/arquivos/<token>`).
"""
import base64
import contextvars
import hashlib
import hmac
import json
import mimetypes
import os
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings, get_settings
from app.services.storage.base import StorageClient, validate_key
from app.services.storage.s3_client import (
    DEFAULT_PRESIGNED_URL_EXPIRES_IN_SECONDS,
    MAX_UPLOAD_SIZE_BYTES,
    ObjectNotFoundError,
)

ARQUIVOS_PATH = "/api/v1/arquivos"
_ASSINATURA_CONTEXTO = b"garra-storage-download-v1"

# Base URL (esquema + host) do request em curso; preenchida pelo middleware.
request_base_url: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_base_url", default=None
)

_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def content_type_da_chave(key: str) -> str:
    ext = Path(key).suffix.lower()
    return _CONTENT_TYPES.get(ext) or mimetypes.guess_type(key)[0] or "application/octet-stream"


def _b64(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode("ascii")


def _unb64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _chave_hmac(settings: Settings) -> bytes:
    return hmac.new(
        settings.jwt_secret_key.encode("utf-8"), _ASSINATURA_CONTEXTO, hashlib.sha256
    ).digest()


def assinar_token(key: str, expires_in: int, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    payload = json.dumps({"k": key, "e": int(time.time()) + expires_in}, separators=(",", ":"))
    corpo = _b64(payload.encode("utf-8"))
    mac = hmac.new(_chave_hmac(settings), corpo.encode("ascii"), hashlib.sha256).digest()
    return f"{corpo}.{_b64(mac)}"


def validar_token(token: str, settings: Settings | None = None) -> str | None:
    """Retorna a chave se o token for íntegro e não vencido; senão `None`."""
    settings = settings or get_settings()
    try:
        corpo, mac_b64 = token.split(".", 1)
        esperado = hmac.new(_chave_hmac(settings), corpo.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(esperado, _unb64(mac_b64)):
            return None
        payload = json.loads(_unb64(corpo))
        if int(payload["e"]) < time.time():
            return None
        chave = payload["k"]
        return chave if isinstance(chave, str) and chave else None
    except (ValueError, KeyError, TypeError, UnicodeError):
        return None


class LocalStorageClient(StorageClient):
    """Objetos como arquivos sob `STORAGE_LOCAL_DIR`, chave = caminho relativo (`/`)."""

    def __init__(self, settings: Settings | None = None, root: Path | None = None) -> None:
        self._settings = settings or get_settings()
        self._root = Path(root or self._settings.storage_local_dir).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        validate_key(key)
        destino = (self._root / key).resolve()
        if destino == self._root or not destino.is_relative_to(self._root):
            raise ValueError("Chave inválida: fora do diretório de armazenamento.")
        return destino

    def upload(
        self, key: str, file_bytes: bytes, content_type: str, *, max_size_bytes: int | None = None
    ) -> str:
        destino = self._path(key)
        if not file_bytes:
            raise ValueError("O conteúdo do arquivo não pode ser vazio.")
        limite = max_size_bytes if max_size_bytes is not None else MAX_UPLOAD_SIZE_BYTES
        if len(file_bytes) > limite:
            raise ValueError(
                f"Arquivo de {len(file_bytes)} bytes excede o limite máximo de "
                f"{limite} bytes por objeto."
            )
        destino.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=destino.parent, prefix=".tmp-")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(file_bytes)
            os.replace(tmp, destino)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        return key

    def download(self, key: str) -> bytes:
        destino = self._path(key)
        if not destino.is_file():
            raise ObjectNotFoundError(f"Objeto '{key}' não encontrado.")
        return destino.read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def _arquivos(self, prefix: str):
        for p in self._root.rglob("*"):
            if p.is_file() and not p.name.startswith(".tmp-"):
                chave = p.relative_to(self._root).as_posix()
                if chave.startswith(prefix):
                    yield chave, p

    def list_keys(self, prefix: str = "") -> list[str]:
        return sorted(chave for chave, _ in self._arquivos(prefix))

    def list_objects(self, prefix: str = "") -> list[tuple[str, datetime]]:
        return sorted(
            (chave, datetime.fromtimestamp(p.stat().st_mtime, tz=UTC))
            for chave, p in self._arquivos(prefix)
        )

    def generate_presigned_url(
        self, key: str, expires_in: int = DEFAULT_PRESIGNED_URL_EXPIRES_IN_SECONDS
    ) -> str:
        validate_key(key)
        if expires_in <= 0:
            raise ValueError("expires_in deve ser um número de segundos positivo.")
        base = (self._settings.public_base_url or request_base_url.get() or "").rstrip("/")
        return f"{base}{ARQUIVOS_PATH}/{assinar_token(key, expires_in, self._settings)}"

    def caminho_para_download(self, key: str) -> Path | None:
        """Caminho do arquivo se existir (uso do endpoint de download)."""
        destino = self._path(key)
        return destino if destino.is_file() else None
