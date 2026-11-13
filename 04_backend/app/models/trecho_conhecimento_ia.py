"""Modelo `TrechoConhecimentoIA` — base de referência do RAG da legenda IA (BL-34, IA-05).

Trechos anonimizados de relatórios históricos (`00_docs/convertidos/*.md`) e de NBRs, buscados por
texto (FTS `portuguese` + `pg_trgm`, migration c6f2a8d4e1b9). `tsv` é gerada pelo banco; `hash`
(sha256 do texto) é único e torna a ingestão idempotente.
"""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Computed, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

TIPOS_TRECHO = ("relatorio_historico", "nbr")


class TrechoConhecimentoIA(Base):
    __tablename__ = "trechos_conhecimento_ia"
    __table_args__ = (
        UniqueConstraint("hash", name="uq_trechos_conhecimento_ia_hash"),
        CheckConstraint("tipo IN ('relatorio_historico', 'nbr')", name="ck_trechos_conhecimento_ia_tipo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fonte: Mapped[str] = mapped_column(String(300), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    sistema: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tipo_anomalia: Mapped[str | None] = mapped_column(String(120), nullable=True)
    grau_risco: Mapped[str | None] = mapped_column(String(30), nullable=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('portuguese'::regconfig, texto)", persisted=True), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
