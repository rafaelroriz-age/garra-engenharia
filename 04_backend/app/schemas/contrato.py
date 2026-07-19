"""Schemas Pydantic v2 de `Contrato` (request/response), sem lógica de negócio."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ContratoBase(BaseModel):
    edificacao_id: uuid.UUID
    fiscal_id: uuid.UUID
    numero: str
    tipo_servico: str
    objeto: str | None = None
    data_inicio: date | None = None
    prazo_dias: int | None = None
    art_fiscalizacao: str | None = None
    observacoes_gerais: str | None = None
    status: str


class ContratoCreate(ContratoBase):
    pass


class ContratoRead(ContratoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
