"""Modelo `VisitaMedicao` — medição de serviço executado registrada em uma Visita."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.visita import Visita


class VisitaMedicao(Base):
    """Medição (quantidade + unidade) de um serviço executado em uma Visita."""

    __tablename__ = "visita_medicoes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visita_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visitas.id"), nullable=False
    )
    descricao: Mapped[str] = mapped_column(String, nullable=False)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    unidade: Mapped[str] = mapped_column(String, nullable=False)

    visita: Mapped["Visita"] = relationship(back_populates="medicoes")
