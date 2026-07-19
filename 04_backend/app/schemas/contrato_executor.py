"""Schemas Pydantic v2 de `ContratoExecutor` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict


class ContratoExecutorBase(BaseModel):
    contrato_id: uuid.UUID
    responsavel_legal_id: uuid.UUID
    rte_id: uuid.UUID | None = None
    razao_social: str
    cnpj: str
    endereco: str | None = None
    art_execucao: str | None = None


class ContratoExecutorCreate(ContratoExecutorBase):
    pass


class ContratoExecutorRead(ContratoExecutorBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
