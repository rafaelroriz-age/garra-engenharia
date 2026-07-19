"""Schemas Pydantic v2 de `Visita` (request/response), sem lógica de negócio."""
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class VisitaBase(BaseModel):
    inspecao_id: uuid.UUID
    data: date
    servicos_executados: str | None = None
    observacoes: str | None = None
    seq_numero: int


class VisitaCreate(VisitaBase):
    pass


class VisitaRead(VisitaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
