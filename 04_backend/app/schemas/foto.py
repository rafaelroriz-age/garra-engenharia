"""Schemas Pydantic v2 de `Foto` (request/response), sem lógica de negócio."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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

    imagem_base64: str


class FotoVincularPayload(BaseModel):
    """Payload de `POST /ocorrencias/{id}/fotos` e `POST /visitas/{id}/fotos` (BL-11).

    Vincula um objeto já enviado ao storage (via `/fotos/upload` ou
    `/fotos/upload-clipboard`) a uma Ocorrência ou Visita, criando o registro `Foto`.
    """

    storage_key: str
    legenda: str | None = None
    ordem: int | None = None
    origem: str


class FotoUpdatePayload(BaseModel):
    """Payload de `PUT /fotos/{id}` — atualiza apenas legenda e/ou ordem."""

    legenda: str | None = None
    ordem: int | None = None
