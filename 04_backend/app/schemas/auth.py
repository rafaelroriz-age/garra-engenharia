"""Schemas Pydantic v2 de autenticação (login, token JWT — BL-06, RNF-05)."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
