"""Modelo `ContratoExecutor` — empresa executora (subcontratada) vinculada a um Contrato.

Um Contrato pode ter mais de uma empresa executora, cada uma com Responsável
Legal e RTE próprios (RN-06, RN-09 em `00_docs/estudo-do-contexto.md` Seção 5).
"""
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ContratoExecutor(Base):
    """Empresa executora (subcontratada) de um Contrato, com seu Responsável Legal e RTE."""

    __tablename__ = "contrato_executores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contrato_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contratos.id"), nullable=False
    )
    responsavel_legal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("responsaveis.id"), nullable=False
    )
    rte_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("responsaveis.id"), nullable=True
    )
    razao_social: Mapped[str] = mapped_column(String, nullable=False)
    cnpj: Mapped[str] = mapped_column(String, nullable=False)
    endereco: Mapped[str] = mapped_column(String, nullable=True)
    art_execucao: Mapped[str] = mapped_column(String, nullable=True)

    contrato: Mapped["Contrato"] = relationship(back_populates="executores")
    responsavel_legal: Mapped["Responsavel"] = relationship(
        back_populates="execucoes_como_responsavel_legal",
        foreign_keys=[responsavel_legal_id],
    )
    rte: Mapped["Responsavel | None"] = relationship(
        back_populates="execucoes_como_rte",
        foreign_keys=[rte_id],
    )
