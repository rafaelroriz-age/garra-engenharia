"""Schemas Pydantic v2 de `PromptIA` (BL-36; ADR-12, DEC-21, DEC-37), sem lógica de negócio.

Não há schema de atualização: cada versão é imutável (DEC-37 DP-2); uma nova versão é uma
nova linha, e a ativação é responsabilidade do serviço (BL-37).
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

PROMPT_NOME_MAX_LENGTH = 100
PROMPT_VERSAO_MAX_LENGTH = 50


class PromptIABase(BaseModel):
    nome: str = Field(min_length=1, max_length=PROMPT_NOME_MAX_LENGTH)
    versao: str = Field(min_length=1, max_length=PROMPT_VERSAO_MAX_LENGTH)
    conteudo: str = Field(min_length=1)


class PromptIACreate(PromptIABase):
    ativo: bool = False


class PromptIARead(PromptIABase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ativo: bool
    created_at: datetime
    # Somente leitura: auditoria vem do usuário autenticado, nunca do payload (RN-18).
    criado_por_id: uuid.UUID | None = None
