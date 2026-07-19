"""Schemas Pydantic v2 de `Localizacao` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict


class LocalizacaoBase(BaseModel):
    nome: str
    ordem: int


class LocalizacaoCreate(LocalizacaoBase):
    pass


class LocalizacaoRead(LocalizacaoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
