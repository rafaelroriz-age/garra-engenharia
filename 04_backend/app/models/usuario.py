"""Modelo `Usuario` — conta de login do sistema (autenticação, BL-06/RNF-05).

Entidade nova, fora do diagrama ER original (`00_docs/arquitetura.md` Seção 3):
representa quem acessa o sistema (uso individual ou pequena equipe), distinta
de `Responsavel` (fiscal/RTE/responsável legal — apenas dado de referência do
contrato, sem credenciais). Ver DEC-15 (`00_docs/projeto/decisoes.md`).
"""
import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Usuario(Base):
    """Conta de login (email + hash de senha) usada para autenticação JWT."""

    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
