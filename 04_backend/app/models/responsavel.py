"""Modelo `Responsavel` — pessoa física/jurídica responsável técnica ou legal
(fiscal de contrato, responsável legal de executora, RTE de execução).

Ver `00_docs/arquitetura.md` Seção 3 (Diagrama ER).
"""
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.contrato import Contrato
    from app.models.contrato_executor import ContratoExecutor
    from app.models.usuario import Usuario


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
    # Bloco de assinatura dos laudos (V1-01): título ("Engenheiro Civil"), lista de
    # qualificações (uma por linha na assinatura) e a imagem da assinatura no storage.
    titulo_profissional: Mapped[str | None] = mapped_column(String, nullable=True)
    qualificacoes: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    assinatura_storage_key: Mapped[str | None] = mapped_column(String, nullable=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True, unique=True
    )

    usuario: Mapped["Usuario | None"] = relationship(back_populates="responsavel")
    contratos_como_fiscal: Mapped[list["Contrato"]] = relationship(
        back_populates="fiscal",
        foreign_keys="Contrato.fiscal_id",
    )
    contratos_como_contratante: Mapped[list["Contrato"]] = relationship(
        back_populates="contratante",
        foreign_keys="Contrato.contratante_id",
    )
    execucoes_como_responsavel_legal: Mapped[list["ContratoExecutor"]] = relationship(
        back_populates="responsavel_legal",
        foreign_keys="ContratoExecutor.responsavel_legal_id",
    )
    execucoes_como_rte: Mapped[list["ContratoExecutor"]] = relationship(
        back_populates="rte",
        foreign_keys="ContratoExecutor.rte_id",
    )
