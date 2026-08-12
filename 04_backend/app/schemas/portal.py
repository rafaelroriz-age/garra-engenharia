"""Schemas do Portal do Cliente (BL-32/BL-33, RF-13, RN-14).

Todos os schemas aqui são de LEITURA — o Portal do Cliente é somente leitura
(ver `00_docs/arquitetura.md` Seção 4, "Portal do Cliente").
"""
import uuid
from datetime import date, datetime

from pydantic import BaseModel


class PortalVisitaResumo(BaseModel):
    id: uuid.UUID
    seq_numero: int
    data: date
    servicos_executados: str | None = None
    total_fotos: int


class PortalOcorrenciaResumo(BaseModel):
    id: uuid.UUID
    seq_numero: int
    sistema_nome: str | None = None
    subsistema_nome: str | None = None
    localizacao: str | None = None
    situacao: str
    grau_risco: str | None = None
    prioridade: int | None = None
    descricao: str | None = None


class PortalContagemGrauRisco(BaseModel):
    minimo: int = 0
    medio: int = 0
    critico: int = 0


class PortalContratoAcompanhamento(BaseModel):
    contrato_id: uuid.UUID
    numero: str
    tipo_servico: str
    status: str
    data_inicio: date | None = None
    inspecao_id: uuid.UUID | None = None
    inspecao_status: str | None = None
    total_visitas: int
    total_ocorrencias: int
    ocorrencias_por_grau_risco: PortalContagemGrauRisco
    visitas: list[PortalVisitaResumo]
    ocorrencias: list[PortalOcorrenciaResumo]


class PortalAcompanhamentoRead(BaseModel):
    edificacao_id: uuid.UUID
    edificacao_nome: str | None = None
    contratos: list[PortalContratoAcompanhamento]


class PortalRelatorioRead(BaseModel):
    id: uuid.UUID
    versao: str
    tipo: str
    status: str
    emitido_em: datetime | None = None
    tem_pdf: bool
    tem_docx: bool
    inspecao_id: uuid.UUID
    contrato_id: uuid.UUID
    contrato_numero: str
    edificacao_id: uuid.UUID
    edificacao_nome: str | None = None


class PortalDownloadRead(BaseModel):
    """URL pré-assinada de download, de curta duração (Seção 10.1, A02)."""

    relatorio_id: uuid.UUID
    formato: str
    url: str
    expira_em_segundos: int
