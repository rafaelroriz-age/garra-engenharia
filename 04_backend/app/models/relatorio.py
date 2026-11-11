"""Modelo `Relatorio` — versão emitida (PDF/DOCX) de uma Inspeção (RF-06)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Relatorio(Base):
    """Relatório/laudo emitido (PDF e/ou DOCX) para uma Inspeção."""

    __tablename__ = "relatorios"
    __table_args__ = (
        UniqueConstraint("inspecao_id", "tipo", "versao", name="uq_relatorios_inspecao_tipo_versao"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspecao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspecoes.id"), nullable=False
    )
    versao: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    pdf_key: Mapped[str] = mapped_column(String, nullable=True)
    docx_key: Mapped[str] = mapped_column(String, nullable=True)
    emitido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    inspecao: Mapped["Inspecao"] = relationship(back_populates="relatorios")
