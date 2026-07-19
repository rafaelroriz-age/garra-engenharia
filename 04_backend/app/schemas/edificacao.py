"""Schemas Pydantic v2 de `Edificacao` (request/response), sem lógica de negócio.

Validações de regras de negócio (RN-XX) são adicionadas nas tarefas de CRUD
(BL-08 em diante), não nesta etapa (BL-04).
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


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


class EdificacaoRead(EdificacaoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
