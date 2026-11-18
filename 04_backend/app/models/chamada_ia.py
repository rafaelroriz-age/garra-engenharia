"""Modelo `ChamadaIA` — telemetria de custo e cache local da legenda por IA (BL-34, R-10).

Uma linha por geração: tokens, custo estimado, latência e origem (`api` | `cache_local`).
`resposta` guarda o resultado já saneado (serve de cache); nunca guarda chave de API nem o
prompt/contexto enviados.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

FINALIDADES_IA = ("legenda_foto",)
ORIGENS_IA = ("api", "cache_local")


class ChamadaIA(Base):
    __tablename__ = "chamadas_ia"
    __table_args__ = (
        CheckConstraint("finalidade IN ('legenda_foto')", name="ck_chamadas_ia_finalidade"),
        CheckConstraint("origem IN ('api', 'cache_local')", name="ck_chamadas_ia_origem"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    foto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fotos.id", ondelete="SET NULL"), nullable=True
    )
    finalidade: Mapped[str] = mapped_column(String(30), nullable=False, default="legenda_foto")
    provedor: Mapped[str] = mapped_column(String(30), nullable=False)
    modelo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    modo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    prompt_ia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompts_ia.id"), nullable=True
    )
    prompt_conteudo_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    chave_cache: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    origem: Mapped[str] = mapped_column(String(20), nullable=False)
    sucesso: Mapped[bool] = mapped_column(Boolean, nullable=False)
    erro_tipo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_prompt: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    tokens_cache_hit: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    tokens_cache_miss: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    tokens_saida: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    custo_estimado_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    latencia_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    resposta: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
