"""Modelo `Inspecao` — processo de inspeção originado de um Contrato (RFO, LTIP, etc.).

Relação 1:1 com Contrato (`CONTRATO ||--|| INSPECAO : "origina"`), ver
`00_docs/arquitetura.md` Seção 3.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Inspecao(Base):
    """Inspeção (RFO, LTIP, Vistoria Cautelar etc.) originada de um Contrato."""

    __tablename__ = "inspecoes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contrato_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contratos.id"), nullable=False, unique=True
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contrato: Mapped["Contrato"] = relationship(back_populates="inspecao")
    visitas: Mapped[list["Visita"]] = relationship(back_populates="inspecao")
    ocorrencias: Mapped[list["Ocorrencia"]] = relationship(back_populates="inspecao")
    relatorios: Mapped[list["Relatorio"]] = relationship(back_populates="inspecao")
