"""chamadas_ia_telemetria_bl_34

BL-34 / R-10: tabela `chamadas_ia` com tokens, custo estimado, latência e origem (`api` |
`cache_local`) de cada geração de legenda por IA; `resposta` (JSONB, saneada) alimenta o cache local.
`foto_id` usa ON DELETE SET NULL: apagar a foto preserva o histórico de custo.

`downgrade()` remove índice e tabela (os dados de telemetria são descartados).

Revision ID: b8d4f2a6c1e7
Revises: a9c3e5f7b1d2
Create Date: 2026-11-11 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b8d4f2a6c1e7"
down_revision: str | Sequence[str] | None = "a9c3e5f7b1d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chamadas_ia",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("foto_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("finalidade", sa.String(30), nullable=False),
        sa.Column("provedor", sa.String(30), nullable=False),
        sa.Column("modelo", sa.String(100), nullable=True),
        sa.Column("modo", sa.String(20), nullable=True),
        sa.Column("prompt_ia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("prompt_conteudo_hash", sa.String(64), nullable=True),
        sa.Column("chave_cache", sa.String(64), nullable=False),
        sa.Column("origem", sa.String(20), nullable=False),
        sa.Column("sucesso", sa.Boolean(), nullable=False),
        sa.Column("erro_tipo", sa.String(100), nullable=True),
        sa.Column("tokens_prompt", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tokens_cache_hit", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tokens_cache_miss", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tokens_saida", sa.Integer(), server_default="0", nullable=False),
        sa.Column("custo_estimado_usd", sa.Numeric(12, 6), nullable=True),
        sa.Column("latencia_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("resposta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chamadas_ia")),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name=op.f("fk_chamadas_ia_usuario_id_usuarios")),
        sa.ForeignKeyConstraint(
            ["foto_id"], ["fotos.id"], name=op.f("fk_chamadas_ia_foto_id_fotos"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["prompt_ia_id"], ["prompts_ia.id"], name=op.f("fk_chamadas_ia_prompt_ia_id_prompts_ia")
        ),
        sa.CheckConstraint("finalidade IN ('legenda_foto')", name="ck_chamadas_ia_finalidade"),
        sa.CheckConstraint("origem IN ('api', 'cache_local')", name="ck_chamadas_ia_origem"),
    )
    op.create_index(op.f("ix_chamadas_ia_chave_cache"), "chamadas_ia", ["chave_cache"])


def downgrade() -> None:
    op.drop_index(op.f("ix_chamadas_ia_chave_cache"), table_name="chamadas_ia")
    op.drop_table("chamadas_ia")
