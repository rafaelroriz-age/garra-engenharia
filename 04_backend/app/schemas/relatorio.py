"""Schemas Pydantic v2 de `Relatorio` (request/response), sem lógica de negócio."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.portal import PortalDownloadRead


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
    # Ids das fotos do relatório com legenda IA em rascunho (BL-38); alerta, não bloqueio.
    fotos_ia_em_rascunho: list[uuid.UUID] = []


class RelatorioVersaoRead(BaseModel):
    """Item de `GET /inspecoes/{id}/relatorios` (V1-02): versão emitida, sem as chaves do storage."""

    id: uuid.UUID
    tipo: str
    versao: str
    status: str
    emitido_em: datetime | None = None
    tem_pdf: bool
    tem_docx: bool


class RelatorioDownloadRead(PortalDownloadRead):
    """URL pré-assinada de download para a equipe interna (V1-02); mesmo formato do portal."""
