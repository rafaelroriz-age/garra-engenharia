"""Modelo `Foto` — fotografia vinculada a uma Ocorrência (LTIP) e/ou a uma Visita (RFO).

Ver RN-03, RN-08, RN-11 em `00_docs/estudo-do-contexto.md` Seção 5. Campos de legenda
assistida por IA (RF-15, RN-16, RN-17; ADR-12; DEC-37; BL-36) no bloco final.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ocorrencia import Ocorrencia
    from app.models.prompt_ia import PromptIA
    from app.models.visita import Visita

# DEC-37 (DP-1): NULL = sem sugestão de IA. Só `aprovada` pode compor relatório (RN-16).
STATUS_VALIDACAO_IA = ("rascunho", "aprovada")
# Níveis de certeza do prompt-sistema do cliente (RF-15, ADR-12), em ASCII.
NIVEIS_CERTEZA_IA = ("constatacao_direta", "indicio_tecnico", "hipotese_tecnica", "causa_comprovada")


def _in(coluna: str, valores: tuple[str, ...]) -> str:
    lista = ", ".join(f"'{v}'" for v in valores)
    return f"{coluna} IS NULL OR {coluna} IN ({lista})"


class Foto(Base):
    """Fotografia de inspeção, vinculada a uma Ocorrência e/ou a uma Visita."""

    __tablename__ = "fotos"
    # R-15: uma storage_key só pode estar vinculada a uma Foto.
    __table_args__ = (
        UniqueConstraint("storage_key", name="uq_fotos_storage_key"),
        CheckConstraint(_in("status_validacao_ia", STATUS_VALIDACAO_IA), name="ck_fotos_status_validacao_ia"),
        CheckConstraint(_in("nivel_certeza_ia", NIVEIS_CERTEZA_IA), name="ck_fotos_nivel_certeza_ia"),
        CheckConstraint(
            "status_validacao_ia IS NULL OR legenda_ia_sugerida IS NOT NULL",
            name="ck_fotos_status_ia_exige_sugestao",
        ),
        CheckConstraint(
            "status_validacao_ia IS DISTINCT FROM 'aprovada' "
            "OR (aprovado_por_id IS NOT NULL AND aprovado_em IS NOT NULL)",
            name="ck_fotos_aprovada_exige_aprovador",
        ),
        CheckConstraint(
            "prompt_conteudo_hash IS NULL OR prompt_conteudo_hash ~ '^[0-9a-f]{64}$'",
            name="ck_fotos_prompt_conteudo_hash",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ocorrencia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ocorrencias.id"), nullable=True
    )
    visita_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visitas.id"), nullable=True
    )
    storage_key: Mapped[str] = mapped_column(String, nullable=False)
    url_publica: Mapped[str] = mapped_column(String, nullable=True)
    # Legenda final do relatório. A sugestão da IA nunca é gravada aqui automaticamente (RF-15, DP-4).
    legenda: Mapped[str] = mapped_column(Text, nullable=True)
    origem: Mapped[str] = mapped_column(String, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Autoria de campo (RN-18/DEC-27): quem coletou o dado, distinto de quem emite o relatório.
    criado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )

    # --- Legenda assistida por IA (BL-36) — todos anuláveis; NULL = sem sugestão ---
    # Anotação de campo / transcrição do auditor enviada ao LLM (RN-17: texto bruto original).
    legenda_bruta: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Minuta devolvida pela IA, preservada mesmo após a aprovação (RN-17: sugestão da IA).
    legenda_ia_sugerida: Mapped[str | None] = mapped_column(Text, nullable=True)
    nivel_certeza_ia: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status_validacao_ia: Mapped[str | None] = mapped_column(String(20), nullable=True)
    alertas_ia: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    pendencias_ia: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Versão do prompt-sistema usada (RN-17). RESTRICT: versão referenciada não pode ser apagada.
    prompt_ia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompts_ia.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    # SHA-256 (hex) do conteúdo do prompt efetivamente enviado (DEC-37 DP-2).
    prompt_conteudo_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    legenda_ia_gerada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Quem aprovou/editou e quando (RN-17, DP-3): vem do token, nunca do payload.
    aprovado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    aprovado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ocorrencia: Mapped["Ocorrencia | None"] = relationship(back_populates="fotos")
    visita: Mapped["Visita | None"] = relationship(back_populates="fotos")
    prompt_ia: Mapped["PromptIA | None"] = relationship()
