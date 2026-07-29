"""Schemas Pydantic v2 de `Responsavel` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict


class ResponsavelBase(BaseModel):
    nome: str
    tipo: str
    cpf_cnpj: str | None = None
    crea: str | None = None
    email: str | None = None
    telefone: str | None = None
    usuario_id: uuid.UUID | None = None


class ResponsavelCreate(ResponsavelBase):
    pass


class ResponsavelRead(ResponsavelBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
