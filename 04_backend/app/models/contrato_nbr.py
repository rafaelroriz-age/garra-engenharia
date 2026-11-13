"""Modelo `ContratoNbr` — norma NBR associada a um Contrato (RF-12)."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.contrato import Contrato


class ContratoNbr(Base):
    """Norma técnica NBR aplicável a um Contrato."""

    __tablename__ = "contrato_nbrs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contrato_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contratos.id"), nullable=False
    )
    codigo_nbr: Mapped[str] = mapped_column(String, nullable=False)
    descricao: Mapped[str] = mapped_column(String, nullable=True)

    contrato: Mapped["Contrato"] = relationship(back_populates="nbrs")
