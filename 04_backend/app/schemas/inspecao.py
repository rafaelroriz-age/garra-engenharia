"""Schemas Pydantic v2 de `Inspecao` (request/response), sem lógica de negócio."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.tipo_servico import TipoServico
from app.schemas.visita import VisitaComDetalhes


class InspecaoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    contrato_id: uuid.UUID
    tipo: TipoServico
    status: str


class InspecaoCreate(InspecaoBase):
    pass


class InspecaoRead(InspecaoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    # Leitura tolerante a valores anteriores a V1-01 (ver ContratoRead).
    tipo: TipoServico | str
    id: uuid.UUID
    created_at: datetime


class InspecaoDetalhe(InspecaoRead):
    """Detalhe da Inspeção com as Visitas (ordenadas por `seq_numero`) e seus detalhes (BL-10)."""

    visitas: list[VisitaComDetalhes] = []
