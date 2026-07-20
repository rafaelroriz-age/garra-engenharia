"""Schemas Pydantic v2 de `Visita` (request/response), sem lógica de negócio."""
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.foto import FotoRead
from app.schemas.visita_mao_obra import VisitaMaoObraRead
from app.schemas.visita_medicao import VisitaMedicaoRead


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


class VisitaCreatePayload(BaseModel):
    """Payload de `POST /inspecoes/{id}/visitas` — `inspecao_id` vem do path e
    `seq_numero` é atribuído automaticamente pelo backend (RN-01, BL-10)."""

    data: date
    servicos_executados: str
    observacoes: str | None = None

    @field_validator("servicos_executados")
    @classmethod
    def _servicos_executados_obrigatorio(cls, valor: str) -> str:
        if not valor or not valor.strip():
            raise ValueError("Serviços executados é obrigatório (RN-02).")
        return valor


class VisitaUpdatePayload(BaseModel):
    """Payload de `PUT /visitas/{id}` — atualiza os campos próprios da visita."""

    data: date
    servicos_executados: str
    observacoes: str | None = None

    @field_validator("servicos_executados")
    @classmethod
    def _servicos_executados_obrigatorio(cls, valor: str) -> str:
        if not valor or not valor.strip():
            raise ValueError("Serviços executados é obrigatório (RN-02).")
        return valor


class VisitaComDetalhes(VisitaRead):
    """Visita com equipe, medições e fotos vinculadas (BL-10)."""

    mao_obra: list[VisitaMaoObraRead] = []
    medicoes: list[VisitaMedicaoRead] = []
    fotos: list[FotoRead] = []
