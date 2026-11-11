"""Modelo `RelatorioConteudo` — textos narrativos e dados editoriais de um relatório (V1-01).

Um registro por (inspeção, tipo de relatório). `dados` guarda só o que o auditor
editou; os textos padrão do tipo ficam em
`app/services/report_generator/textos_padrao/*.json` e são mesclados na leitura
(`relatorio_conteudo_service.obter`). O contrato de `dados` está em
`00_docs/backlog-auto/v1-fundacao-dados.md`.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.inspecao import Inspecao
    from app.models.usuario import Usuario


class RelatorioConteudo(Base):
    """Conteúdo editável (textos, datas, parecer) de um tipo de relatório de uma Inspeção."""

    __tablename__ = "relatorio_conteudos"
    __table_args__ = (
        UniqueConstraint("inspecao_id", "tipo", name="uq_relatorio_conteudos_inspecao_tipo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspecao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspecoes.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    dados: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    atualizado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    inspecao: Mapped["Inspecao"] = relationship()
    atualizado_por: Mapped["Usuario | None"] = relationship()
