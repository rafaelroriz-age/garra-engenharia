"""Modelo `VisitaMaoObra` — equipe (função + quantidade) presente em uma Visita (RN-02)."""
import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class VisitaMaoObra(Base):
    """Registro de mão de obra (função e quantidade de profissionais) de uma Visita."""

    __tablename__ = "visita_mao_obras"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visita_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visitas.id"), nullable=False
    )
    funcao: Mapped[str] = mapped_column(String, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)

    visita: Mapped["Visita"] = relationship(back_populates="mao_obra")
