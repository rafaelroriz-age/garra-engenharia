"""Modelo `TipoFalha` — gabarito de tipos de falha (RF-10).

Tabela de dados mestre adicional, sem correspondência no diagrama ER original
de `00_docs/arquitetura.md` Seção 3. Ver DEC-13 em `00_docs/projeto/decisoes.md`:
`Ocorrencia.tipo_falha` permanece texto livre (decisão da BL-04); esta tabela
existe apenas para que o gabarito seja um dado mestre editável (RF-10),
consultável via `GET /api/v1/gabarito/tipos-falha`.
"""
import uuid

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TipoFalha(Base):
    """Tipo de falha do gabarito de inspeção (ex.: De Execução, De Planejamento, Gerencial, Operacional)."""

    __tablename__ = "tipos_falha"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
