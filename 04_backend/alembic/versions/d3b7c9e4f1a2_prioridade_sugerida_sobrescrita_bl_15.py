"""prioridade_sugerida_sobrescrita_bl_15

RN-04/DEC-29 (lacuna #10): a Prioridade da Ocorrência é sugerida a partir do
Grau de Risco CMM e pode ser sobrescrita pelo engenheiro, com registro do valor
sugerido original (`prioridade_sugerida`) e da autoria do ajuste
(`prioridade_ajustada_por_id`/`prioridade_ajustada_em`). Nullable porque os
registros anteriores à decisão não têm sugestão/autoria conhecida.

Revision ID: d3b7c9e4f1a2
Revises: 7c1a4e0b93d5
Create Date: 2026-09-20 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3b7c9e4f1a2"
down_revision: str | Sequence[str] | None = "7c1a4e0b93d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ocorrencias", sa.Column("prioridade_sugerida", sa.Integer(), nullable=True))
    op.add_column("ocorrencias", sa.Column("prioridade_ajustada_por_id", sa.UUID(), nullable=True))
    op.add_column("ocorrencias", sa.Column("prioridade_ajustada_em", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        op.f("fk_ocorrencias_prioridade_ajustada_por_id_usuarios"),
        "ocorrencias",
        "usuarios",
        ["prioridade_ajustada_por_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_ocorrencias_prioridade_ajustada_por_id_usuarios"),
        "ocorrencias",
        type_="foreignkey",
    )
    op.drop_column("ocorrencias", "prioridade_ajustada_em")
    op.drop_column("ocorrencias", "prioridade_ajustada_por_id")
    op.drop_column("ocorrencias", "prioridade_sugerida")
