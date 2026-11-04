"""Modelo `Visita` — visita de acompanhamento (um dia de obra) de uma Inspeção (RFO).

Ver RN-01, RN-02 em `00_docs/estudo-do-contexto.md` Seção 5.
"""
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.foto import Foto
    from app.models.inspecao import Inspecao
    from app.models.visita_mao_obra import VisitaMaoObra
    from app.models.visita_medicao import VisitaMedicao


class Visita(Base):
    """Visita de acompanhamento de obra (um dia) associada a uma Inspeção do tipo RFO."""

    __tablename__ = "visitas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspecao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspecoes.id"), nullable=False
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    servicos_executados: Mapped[str] = mapped_column(Text, nullable=True)
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)
    seq_numero: Mapped[int] = mapped_column(Integer, nullable=False)
    # Autoria de campo (RN-18/DEC-27): quem coletou o dado, distinto de quem emite o relatório.
    criado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )

    inspecao: Mapped["Inspecao"] = relationship(back_populates="visitas")
    mao_obra: Mapped[list["VisitaMaoObra"]] = relationship(back_populates="visita")
    medicoes: Mapped[list["VisitaMedicao"]] = relationship(back_populates="visita")
    fotos: Mapped[list["Foto"]] = relationship(back_populates="visita")
