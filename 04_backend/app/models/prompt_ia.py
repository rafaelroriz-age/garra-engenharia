"""Modelo `PromptIA` — prompt-sistema versionado para legendas assistidas por IA.

Ver RF-15, RN-17 em `00_docs/estudo-do-contexto.md`, ADR-12 em `00_docs/arquitetura.md`
e DEC-21/DEC-37 em `00_docs/projeto/decisoes.md`. Cada versão é uma linha imutável; a troca
de versão é feita alternando `ativo` (no máximo uma versão ativa por `nome`).
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PromptIA(Base):
    """Versão de um prompt-sistema usado na geração de legendas (BL-36)."""

    __tablename__ = "prompts_ia"
    __table_args__ = (
        UniqueConstraint("nome", "versao", name="uq_prompts_ia_nome_versao"),
        # DEC-21 / L19: no máximo uma versão ativa por nome.
        Index("uq_prompts_ia_nome_ativo", "nome", unique=True, postgresql_where=text("ativo")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    versao: Mapped[str] = mapped_column(String(50), nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Auditoria: quem cadastrou a versão (vem do usuário autenticado, nunca do payload).
    criado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
