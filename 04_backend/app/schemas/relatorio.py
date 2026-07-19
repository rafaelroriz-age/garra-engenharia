"""Schemas Pydantic v2 de `Relatorio` (request/response), sem lógica de negócio."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RelatorioBase(BaseModel):
    inspecao_id: uuid.UUID
    versao: str
    tipo: str
    status: str
    pdf_key: str | None = None
    docx_key: str | None = None
    emitido_em: datetime | None = None


class RelatorioCreate(RelatorioBase):
    pass


class RelatorioRead(RelatorioBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
