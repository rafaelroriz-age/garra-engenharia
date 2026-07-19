"""Schemas Pydantic v2 de `ContratoNbr` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict


class ContratoNbrBase(BaseModel):
    contrato_id: uuid.UUID
    codigo_nbr: str
    descricao: str | None = None


class ContratoNbrCreate(ContratoNbrBase):
    pass


class ContratoNbrRead(ContratoNbrBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
