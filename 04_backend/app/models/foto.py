"""Modelo `Foto` — fotografia vinculada a uma Ocorrência (LTIP) e/ou a uma Visita (RFO).

Ver RN-03, RN-08, RN-11 em `00_docs/estudo-do-contexto.md` Seção 5.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Foto(Base):
    """Fotografia de inspeção, vinculada a uma Ocorrência e/ou a uma Visita."""

    __tablename__ = "fotos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ocorrencia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ocorrencias.id"), nullable=True
    )
    visita_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visitas.id"), nullable=True
    )
    storage_key: Mapped[str] = mapped_column(String, nullable=False)
    url_publica: Mapped[str] = mapped_column(String, nullable=True)
    legenda: Mapped[str] = mapped_column(Text, nullable=True)
    origem: Mapped[str] = mapped_column(String, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Autoria de campo (RN-18/DEC-27): quem coletou o dado, distinto de quem emite o relatório.
    criado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )

    ocorrencia: Mapped["Ocorrencia | None"] = relationship(back_populates="fotos")
    visita: Mapped["Visita | None"] = relationship(back_populates="fotos")
