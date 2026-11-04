"""Schemas Pydantic v2 de `Foto` (request/response), sem lógica de negócio."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# DEC-39 (C): domínio fechado de `origem` e tetos de `ordem`/`legenda`.
OrigemFoto = Literal["upload_manual", "lightshot", "clipboard"]
LEGENDA_MAX_LENGTH = 500
# Base64 de MAX_UPLOAD_SIZE_BYTES (25 MB) = ceil(25 MiB / 3) * 4 = 34_952_536 caracteres.
IMAGEM_BASE64_MAX_LENGTH = 34_952_536


class FotoBase(BaseModel):
    ocorrencia_id: uuid.UUID | None = None
    visita_id: uuid.UUID | None = None
    storage_key: str
    url_publica: str | None = None
    legenda: str | None = None
    origem: str
    ordem: int | None = None


class FotoCreate(FotoBase):
    pass


class FotoRead(FotoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    # Somente leitura: a autoria vem do usuário autenticado, nunca do payload (RN-18).
    criado_por_id: uuid.UUID | None = None


class FotoUploadResponse(BaseModel):
    """Resposta de `POST /fotos/upload` e `POST /fotos/upload-clipboard` (BL-11).

    Apenas envia o arquivo ao storage e devolve a chave + URL pré-assinada —
    ainda não cria o registro `Foto` (isso é feito ao vincular a uma
    Ocorrência ou Visita, ver `FotoVincularPayload`).
    """

    storage_key: str
    url: str


class FotoUploadClipboardPayload(BaseModel):
    """Payload de `POST /fotos/upload-clipboard` — imagem em base64 (Opção A, clipboard paste)."""

    imagem_base64: str = Field(max_length=IMAGEM_BASE64_MAX_LENGTH)


class FotoVincularPayload(BaseModel):
    """Payload de `POST /ocorrencias/{id}/fotos` e `POST /visitas/{id}/fotos` (BL-11).

    Vincula um objeto já enviado ao storage (via `/fotos/upload` ou
    `/fotos/upload-clipboard`) a uma Ocorrência ou Visita, criando o registro `Foto`.
    """

    storage_key: str = Field(max_length=255)
    legenda: str | None = Field(default=None, max_length=LEGENDA_MAX_LENGTH)
    ordem: int | None = Field(default=None, ge=0)
    origem: OrigemFoto


class FotoDescartarUploadPayload(BaseModel):
    """Payload de `DELETE /fotos/upload` — descarta upload que nunca foi vinculado (DEC-39 D)."""

    storage_key: str = Field(max_length=255)


class FotoUpdatePayload(BaseModel):
    """Payload de `PUT /fotos/{id}` — atualiza apenas legenda e/ou ordem."""

    legenda: str | None = Field(default=None, max_length=LEGENDA_MAX_LENGTH)
    ordem: int | None = Field(default=None, ge=0)
