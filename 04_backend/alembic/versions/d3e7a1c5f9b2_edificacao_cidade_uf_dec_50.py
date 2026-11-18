"""edificacao_cidade_uf_dec_50

DEC-50 (P5): `cidade` (até 120) e `uf` (2) opcionais em `edificacoes`, usadas como local de
emissão dos relatórios quando preenchidas; sem elas a emissão continua extraindo `Cidade-UF`
do `endereco`. As colunas são nullable e a migration não reescreve dados nem faz backfill.

`downgrade()` remove as duas colunas.

Revision ID: d3e7a1c5f9b2
Revises: c6f2a8d4e1b9
Create Date: 2026-11-18 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d3e7a1c5f9b2"
down_revision: str | Sequence[str] | None = "c6f2a8d4e1b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("edificacoes", sa.Column("cidade", sa.String(length=120), nullable=True))
    op.add_column("edificacoes", sa.Column("uf", sa.String(length=2), nullable=True))


def downgrade() -> None:
    op.drop_column("edificacoes", "uf")
    op.drop_column("edificacoes", "cidade")
