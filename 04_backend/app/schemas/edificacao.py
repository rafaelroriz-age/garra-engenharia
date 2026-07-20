"""Schemas Pydantic v2 de `Edificacao` (request/response), sem lógica de negócio.

Validações de regras de negócio (RN-XX) são adicionadas nas tarefas de CRUD
(BL-08 em diante), não nesta etapa (BL-04).
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.contrato import ContratoRead


class EdificacaoBase(BaseModel):
    nome: str
    endereco: str
    cep: str | None = None
    tipologia: str | None = None
    sistema_construtivo: str | None = None
    descricao_pavimentos: str | None = None
    area_total_m2: float | None = None
    documentos_tecnicos: dict[str, Any] | None = None


class EdificacaoCreate(EdificacaoBase):
    pass


class EdificacaoUpdate(EdificacaoBase):
    """Payload de `PUT /edificacoes/{id}` — substitui todos os campos (BL-08)."""


class EdificacaoRead(EdificacaoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class EdificacaoComContratos(EdificacaoRead):
    """Detalhe de Edificação incluindo o histórico de Contratos vinculados (BL-08, RF-01)."""

    contratos: list[ContratoRead] = []
