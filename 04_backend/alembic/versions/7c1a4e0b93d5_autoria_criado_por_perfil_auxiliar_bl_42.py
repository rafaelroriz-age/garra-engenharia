"""autoria_criado_por_perfil_auxiliar_bl_42

Autoria de campo (RN-18/DEC-27): `criado_por_id` em visitas, ocorrências e
fotos. Nullable porque os registros anteriores à decisão não têm autor
conhecido — não se inventa autoria retroativa.

Revision ID: 7c1a4e0b93d5
Revises: 5f9f3cb4d87f
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7c1a4e0b93d5"
down_revision: Union[str, Sequence[str], None] = "5f9f3cb4d87f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABELAS = ("visitas", "ocorrencias", "fotos")


def upgrade() -> None:
    for tabela in _TABELAS:
        op.add_column(tabela, sa.Column("criado_por_id", sa.UUID(), nullable=True))
        op.create_foreign_key(
            op.f(f"fk_{tabela}_criado_por_id_usuarios"),
            tabela,
            "usuarios",
            ["criado_por_id"],
            ["id"],
        )


def downgrade() -> None:
    for tabela in reversed(_TABELAS):
        op.drop_constraint(op.f(f"fk_{tabela}_criado_por_id_usuarios"), tabela, type_="foreignkey")
        op.drop_column(tabela, "criado_por_id")
