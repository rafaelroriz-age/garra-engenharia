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
