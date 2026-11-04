"""Modelo `Ocorrencia` — anomalia/falha identificada em uma Inspeção (LTIP/Vistoria).

Ver RN-03, RN-04, RN-05, RN-10 em `00_docs/estudo-do-contexto.md` Seção 5.
Os campos de classificação (`situacao`, `classificacao`, `tipo_anomalia`,
`tipo_falha`, `grau_risco`) são armazenados como texto livre nesta etapa
(BL-04); as regras de validação (RN-04, RN-05) serão aplicadas nas tarefas de
CRUD (BL-14 em diante), não neste modelo de dados.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.foto import Foto
    from app.models.inspecao import Inspecao
    from app.models.sistema_predial import SistemaPredial
    from app.models.subsistema import Subsistema


class Ocorrencia(Base):
    """Ocorrência (anomalia/falha) identificada em um sistema/subsistema predial durante a Inspeção."""

    __tablename__ = "ocorrencias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspecao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspecoes.id"), nullable=False
    )
    sistema_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sistemas_prediais.id"), nullable=False
    )
    subsistema_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subsistemas.id"), nullable=True
    )
    localizacao: Mapped[str] = mapped_column(String, nullable=True)
    situacao: Mapped[str] = mapped_column(String, nullable=False)
    classificacao: Mapped[str] = mapped_column(String, nullable=False)
    tipo_anomalia: Mapped[str] = mapped_column(String, nullable=True)
    tipo_falha: Mapped[str] = mapped_column(String, nullable=True)
    grau_risco: Mapped[str] = mapped_column(String, nullable=True)
    prioridade: Mapped[int] = mapped_column(Integer, nullable=True)
    # RN-04/DEC-29 (BL-15): prioridade sugerida a partir do Grau de Risco CMM e
    # rastreio da sobrescrita explícita pelo engenheiro (quem e quando ajustou).
    prioridade_sugerida: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prioridade_ajustada_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    prioridade_ajustada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    gut_gravidade: Mapped[float] = mapped_column(Float, nullable=True)
    gut_urgencia: Mapped[float] = mapped_column(Float, nullable=True)
    gut_tendencia: Mapped[float] = mapped_column(Float, nullable=True)
    seq_numero: Mapped[int] = mapped_column(Integer, nullable=False)
    # Autoria de campo (RN-18/DEC-27): quem coletou o dado, distinto de quem emite o relatório.
    criado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )

    inspecao: Mapped["Inspecao"] = relationship(back_populates="ocorrencias")
    sistema: Mapped["SistemaPredial"] = relationship(back_populates="ocorrencias")
    subsistema: Mapped["Subsistema | None"] = relationship(back_populates="ocorrencias")
    fotos: Mapped[list["Foto"]] = relationship(back_populates="ocorrencia")
