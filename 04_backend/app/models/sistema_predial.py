"""Modelo `SistemaPredial` — gabarito de sistemas prediais inspecionados (RF-10)."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ocorrencia import Ocorrencia
    from app.models.subsistema import Subsistema


class SistemaPredial(Base):
    """Sistema predial do gabarito de inspeção (ex.: Elétrico, Hidráulico, Estrutural)."""

    __tablename__ = "sistemas_prediais"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)

    subsistemas: Mapped[list["Subsistema"]] = relationship(back_populates="sistema")
    ocorrencias: Mapped[list["Ocorrencia"]] = relationship(back_populates="sistema")
