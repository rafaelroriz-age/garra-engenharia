"""Schemas Pydantic v2 de `VisitaMedicao` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict


class VisitaMedicaoBase(BaseModel):
    visita_id: uuid.UUID
    descricao: str
    quantidade: float
    unidade: str


class VisitaMedicaoCreate(VisitaMedicaoBase):
    pass


class VisitaMedicaoRead(VisitaMedicaoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class VisitaMedicaoCreatePayload(BaseModel):
    """Payload de `POST /visitas/{id}/medicoes` — `visita_id` vem do path (BL-10)."""

    descricao: str
    quantidade: float
    unidade: str
