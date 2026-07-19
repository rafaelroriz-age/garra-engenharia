"""Schemas Pydantic v2 de `SistemaPredial` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.subsistema import SubsistemaRead


class SistemaPredialBase(BaseModel):
    nome: str
    ordem: int


class SistemaPredialCreate(SistemaPredialBase):
    pass


class SistemaPredialRead(SistemaPredialBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class SistemaPredialComSubsistemas(SistemaPredialRead):
    """Resposta de `GET /api/v1/sistemas-prediais` (RF-10): sistema com seus subsistemas."""

    subsistemas: list[SubsistemaRead] = []
