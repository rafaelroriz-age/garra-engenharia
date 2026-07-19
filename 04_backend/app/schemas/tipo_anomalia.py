"""Schemas Pydantic v2 de `TipoAnomalia` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict


class TipoAnomaliaBase(BaseModel):
    nome: str
    ordem: int


class TipoAnomaliaCreate(TipoAnomaliaBase):
    pass


class TipoAnomaliaRead(TipoAnomaliaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
