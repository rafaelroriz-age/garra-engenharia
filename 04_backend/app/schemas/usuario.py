"""Schemas Pydantic v2 de `Usuario` (autenticação, BL-06)."""
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioBase(BaseModel):
    nome: str = Field(min_length=1)
    email: EmailStr


class UsuarioCreate(UsuarioBase):
    senha: str = Field(min_length=8, description="Senha em texto plano — nunca armazenada nem retornada.")
    # Onboarding dos usuários Cliente (DEC-18) e Auxiliar (DEC-27) é manual, feito por um auditor.
    role: Literal["auditor", "auxiliar", "cliente"] = "auditor"


class UsuarioRead(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ativo: bool
    role: str
