"""Schemas Pydantic v2 de `Subsistema` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict


class SubsistemaBase(BaseModel):
    sistema_id: uuid.UUID
    nome: str
    ordem: int


class SubsistemaCreate(SubsistemaBase):
    pass


class SubsistemaRead(SubsistemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
