"""Schemas Pydantic v2 de `Responsavel` (request/response), sem lógica de negócio."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

# Bloco de assinatura dos laudos (V1-01): tetos para não aceitar payload gigante.
TITULO_PROFISSIONAL_MAX = 120
QUALIFICACAO_MAX = 300
QUALIFICACOES_MAX_ITENS = 20
STORAGE_KEY_MAX = 512


class ResponsavelBase(BaseModel):
    nome: str
    tipo: str
    cpf_cnpj: str | None = None
    crea: str | None = None
    email: str | None = None
    telefone: str | None = None
    usuario_id: uuid.UUID | None = None
    titulo_profissional: str | None = Field(None, max_length=TITULO_PROFISSIONAL_MAX)
    qualificacoes: list[str] | None = Field(None, max_length=QUALIFICACOES_MAX_ITENS)
    assinatura_storage_key: str | None = Field(None, max_length=STORAGE_KEY_MAX)


class ResponsavelCreate(ResponsavelBase):
    pass


class ResponsavelUpdate(BaseModel):
    """Atualização parcial de um Responsável (só os campos enviados mudam)."""

    nome: str | None = None
    tipo: str | None = None
    cpf_cnpj: str | None = None
    crea: str | None = None
    email: str | None = None
    telefone: str | None = None
    usuario_id: uuid.UUID | None = None
    titulo_profissional: str | None = Field(None, max_length=TITULO_PROFISSIONAL_MAX)
    qualificacoes: list[str] | None = Field(None, max_length=QUALIFICACOES_MAX_ITENS)
    assinatura_storage_key: str | None = Field(None, max_length=STORAGE_KEY_MAX)


class ResponsavelRead(ResponsavelBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
