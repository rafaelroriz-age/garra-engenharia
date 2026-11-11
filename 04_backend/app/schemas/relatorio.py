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


class RelatorioEmitirPayload(BaseModel):
    """Corpo (opcional) de `POST /inspecoes/{id}/relatorios/rfo` (BL-13).

    Vazio por ora: tipo, versão e chaves no storage são decididos pelo servidor.
    `extra=forbid` recusa (422) qualquer campo enviado pelo cliente, ex. `pdf_key`.
    """

    model_config = ConfigDict(extra="forbid")


class RelatorioEmitidoRead(BaseModel):
    """Resposta da emissão: não expõe as chaves do storage, só se há arquivo."""

    id: uuid.UUID
    inspecao_id: uuid.UUID
    tipo: str
    versao: str
    status: str
    tem_pdf: bool
    tem_docx: bool
    criado_em: datetime | None = None
