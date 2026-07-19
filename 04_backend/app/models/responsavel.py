"""Modelo `Responsavel` — pessoa física/jurídica responsável técnica ou legal
(fiscal de contrato, responsável legal de executora, RTE de execução).

Ver `00_docs/arquitetura.md` Seção 3 (Diagrama ER).
"""
import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Responsavel(Base):
    """Responsável (engenheiro fiscal, responsável legal ou RTE) vinculado a Contratos."""

    __tablename__ = "responsaveis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    cpf_cnpj: Mapped[str] = mapped_column(String, nullable=True)
    crea: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
    telefone: Mapped[str] = mapped_column(String, nullable=True)

    contratos_como_fiscal: Mapped[list["Contrato"]] = relationship(back_populates="fiscal")
    execucoes_como_responsavel_legal: Mapped[list["ContratoExecutor"]] = relationship(
        back_populates="responsavel_legal",
        foreign_keys="ContratoExecutor.responsavel_legal_id",
    )
    execucoes_como_rte: Mapped[list["ContratoExecutor"]] = relationship(
        back_populates="rte",
        foreign_keys="ContratoExecutor.rte_id",
    )
