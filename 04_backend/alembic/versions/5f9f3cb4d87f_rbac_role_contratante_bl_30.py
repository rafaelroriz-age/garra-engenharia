"""rbac_role_contratante_bl_30

Revision ID: 5f9f3cb4d87f
Revises: ab22bfcbdd0a
Create Date: 2026-07-29 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f9f3cb4d87f"
down_revision: str | Sequence[str] | None = "ab22bfcbdd0a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("role", sa.String(), nullable=False, server_default="auditor"))
    op.add_column("responsaveis", sa.Column("usuario_id", sa.UUID(), nullable=True))
    op.add_column("contratos", sa.Column("contratante_id", sa.UUID(), nullable=True))

    op.create_unique_constraint(op.f("uq_responsaveis_usuario_id"), "responsaveis", ["usuario_id"])
    op.create_foreign_key(
        op.f("fk_responsaveis_usuario_id_usuarios"),
        "responsaveis",
        "usuarios",
        ["usuario_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_contratos_contratante_id_responsaveis"),
        "contratos",
        "responsaveis",
        ["contratante_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_contratos_contratante_id_responsaveis"), "contratos", type_="foreignkey")
    op.drop_constraint(op.f("fk_responsaveis_usuario_id_usuarios"), "responsaveis", type_="foreignkey")
    op.drop_constraint(op.f("uq_responsaveis_usuario_id"), "responsaveis", type_="unique")
    op.drop_column("contratos", "contratante_id")
    op.drop_column("responsaveis", "usuario_id")
    op.drop_column("usuarios", "role")
