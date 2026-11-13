"""Modelo `Subsistema` — gabarito de subsistemas dentro de um Sistema Predial (RF-10)."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ocorrencia import Ocorrencia
    from app.models.sistema_predial import SistemaPredial


class Subsistema(Base):
    """Subsistema do gabarito de inspeção, vinculado a um Sistema Predial."""

    __tablename__ = "subsistemas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sistema_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sistemas_prediais.id"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)

    sistema: Mapped["SistemaPredial"] = relationship(back_populates="subsistemas")
    ocorrencias: Mapped[list["Ocorrencia"]] = relationship(back_populates="subsistema")
