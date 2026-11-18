"""Schemas Pydantic v2 de `Edificacao` (request/response), sem lógica de negócio.

Validações de regras de negócio (RN-XX) são adicionadas nas tarefas de CRUD
(BL-08 em diante), não nesta etapa (BL-04).
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.schemas.contrato import ContratoRead


class EdificacaoBase(BaseModel):
    nome: str
    endereco: str
    cep: str | None = None
    # DEC-50 P5: local de emissão; ausentes, a emissão extrai `Cidade-UF` do `endereco`.
    cidade: str | None = Field(default=None, max_length=120)
    uf: str | None = Field(default=None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    tipologia: str | None = None
    sistema_construtivo: str | None = None
    descricao_pavimentos: str | None = None
    area_total_m2: float | None = None
    documentos_tecnicos: dict[str, Any] | None = None

    @field_validator("cidade", "uf", mode="before")
    @classmethod
    def _normalizar_cidade_uf(cls, valor: Any, info: ValidationInfo) -> Any:
        """Apara espaços; vazio (ou só espaços) vira `None`; `uf` em maiúsculas (`go` → `GO`).

        O `pattern` de `uf` rejeita (422) o que não for exatamente 2 letras A-Z.
        """
        if not isinstance(valor, str):
            return valor
        valor = valor.strip()
        if not valor:
            return None
        return valor.upper() if info.field_name == "uf" else valor


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
