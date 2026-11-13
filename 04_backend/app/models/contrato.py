"""Modelo `Contrato` — contrato de fiscalização/execução firmado sobre uma Edificação.

Ver `00_docs/arquitetura.md` Seção 3 (Diagrama ER) e RN-06, RN-09
(`00_docs/estudo-do-contexto.md` Seção 5).
"""
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.contrato_executor import ContratoExecutor
    from app.models.contrato_nbr import ContratoNbr
    from app.models.edificacao import Edificacao
    from app.models.inspecao import Inspecao
    from app.models.responsavel import Responsavel


class Contrato(Base):
    """Contrato de fiscalização/execução vinculado a uma Edificação e a um fiscal."""

    __tablename__ = "contratos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    edificacao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("edificacoes.id"), nullable=False
    )
    fiscal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("responsaveis.id"), nullable=False
    )
    contratante_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("responsaveis.id"), nullable=True
    )
    numero: Mapped[str] = mapped_column(String, nullable=False)
    tipo_servico: Mapped[str] = mapped_column(String, nullable=False)
    objeto: Mapped[str] = mapped_column(Text, nullable=True)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=True)
    prazo_dias: Mapped[int] = mapped_column(Integer, nullable=True)
    art_fiscalizacao: Mapped[str] = mapped_column(String, nullable=True)
    observacoes_gerais: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    edificacao: Mapped["Edificacao"] = relationship(back_populates="contratos")
    fiscal: Mapped["Responsavel"] = relationship(
        back_populates="contratos_como_fiscal",
        foreign_keys="[Contrato.fiscal_id]",
    )
    contratante: Mapped["Responsavel | None"] = relationship(
        back_populates="contratos_como_contratante",
        foreign_keys="[Contrato.contratante_id]",
    )
    executores: Mapped[list["ContratoExecutor"]] = relationship(back_populates="contrato")
    nbrs: Mapped[list["ContratoNbr"]] = relationship(back_populates="contrato")
    inspecao: Mapped["Inspecao | None"] = relationship(back_populates="contrato", uselist=False)
