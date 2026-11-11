"""Modelo `Edificacao` — entidade raiz do domínio (uma edificação física inspecionada).

Ver `00_docs/arquitetura.md` Seção 3 (Diagrama ER).
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.contrato import Contrato


class Edificacao(Base):
    """Edificação (prédio/condomínio) sobre a qual incidem Contratos de fiscalização."""

    __tablename__ = "edificacoes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    endereco: Mapped[str] = mapped_column(String, nullable=False)
    cep: Mapped[str] = mapped_column(String, nullable=True)
    tipologia: Mapped[str] = mapped_column(String, nullable=True)
    sistema_construtivo: Mapped[str] = mapped_column(String, nullable=True)
    descricao_pavimentos: Mapped[str] = mapped_column(Text, nullable=True)
    area_total_m2: Mapped[float] = mapped_column(Float, nullable=True)
    documentos_tecnicos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contratos: Mapped[list["Contrato"]] = relationship(back_populates="edificacao")
