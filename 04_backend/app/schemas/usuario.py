"""Schemas Pydantic v2 de `Usuario` (autenticação, BL-06)."""
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioBase(BaseModel):
    nome: str = Field(min_length=1)
    email: EmailStr


class UsuarioCreate(UsuarioBase):
    senha: str = Field(min_length=8, description="Senha em texto plano — nunca armazenada nem retornada.")


class UsuarioRead(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ativo: bool
    role: str
