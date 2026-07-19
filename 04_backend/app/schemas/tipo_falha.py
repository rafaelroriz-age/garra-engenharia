"""Schemas Pydantic v2 de `TipoFalha` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict


class TipoFalhaBase(BaseModel):
    nome: str
    ordem: int


class TipoFalhaCreate(TipoFalhaBase):
    pass


class TipoFalhaRead(TipoFalhaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
