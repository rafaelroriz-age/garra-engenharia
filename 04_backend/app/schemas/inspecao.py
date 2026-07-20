"""Schemas Pydantic v2 de `Inspecao` (request/response), sem lógica de negócio."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.visita import VisitaComDetalhes


class InspecaoBase(BaseModel):
    contrato_id: uuid.UUID
    tipo: str
    status: str


class InspecaoCreate(InspecaoBase):
    pass


class InspecaoRead(InspecaoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class InspecaoDetalhe(InspecaoRead):
    """Detalhe da Inspeção com as Visitas (ordenadas por `seq_numero`) e seus detalhes (BL-10)."""

    visitas: list[VisitaComDetalhes] = []
