"""Schemas Pydantic do dashboard de saúde (BL-16, RF-07)."""
import uuid

from pydantic import BaseModel


class DashboardConformidadePorSistema(BaseModel):
    sistema_id: uuid.UUID
    sistema_nome: str
    conforme: int
    nao_conforme: int
    total: int


class DashboardGrauRiscoPorSistema(BaseModel):
    sistema_id: uuid.UUID
    sistema_nome: str
    minimo: int
    medio: int
    critico: int


class DashboardGravidadePorSubsistema(BaseModel):
    subsistema_id: uuid.UUID
    subsistema_nome: str
    sistema_nome: str | None = None
    media_gravidade: float


class DashboardEdificacaoRead(BaseModel):
    edificacao_id: uuid.UUID
    edificacao_nome: str | None = None
    conformidade_por_sistema: list[DashboardConformidadePorSistema]
    grau_risco_por_sistema: list[DashboardGrauRiscoPorSistema]
    gravidade_por_subsistema: list[DashboardGravidadePorSubsistema]
