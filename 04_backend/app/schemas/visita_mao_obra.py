"""Schemas Pydantic v2 de `VisitaMaoObra` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict


class VisitaMaoObraBase(BaseModel):
    visita_id: uuid.UUID
    funcao: str
    quantidade: int


class VisitaMaoObraCreate(VisitaMaoObraBase):
    pass


class VisitaMaoObraRead(VisitaMaoObraBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
