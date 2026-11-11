"""fotos_storage_key_unico_r15

R-15: garante no banco que uma `storage_key` só pode estar vinculada a uma
Foto (antes, só a aplicação garantia). `storage_key` é NOT NULL, então basta
uma restrição UNIQUE comum (sem índice parcial). Se já houver chaves
duplicadas, o upgrade aborta listando-as; nenhum dado é alterado ou apagado.

Revision ID: e5a1c7d9b3f4
Revises: d3b7c9e4f1a2
Create Date: 2026-11-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e5a1c7d9b3f4"
down_revision: Union[str, Sequence[str], None] = "d3b7c9e4f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CONSTRAINT = "uq_fotos_storage_key"


def upgrade() -> None:
    bind = op.get_bind()
    duplicadas = bind.execute(
        sa.text(
            "SELECT storage_key, count(*) FROM fotos "
            "WHERE storage_key IS NOT NULL "
            "GROUP BY storage_key HAVING count(*) > 1 ORDER BY storage_key"
        )
    ).fetchall()
    if duplicadas:
        lista = ", ".join(f"{chave} (x{qtd})" for chave, qtd in duplicadas)
        raise RuntimeError(
            f"Impossível criar UNIQUE(storage_key): {len(duplicadas)} chave(s) duplicada(s) em fotos: "
            f"{lista}. Resolva manualmente; nenhum dado foi alterado."
        )
    op.create_unique_constraint(_CONSTRAINT, "fotos", ["storage_key"])


def downgrade() -> None:
    op.drop_constraint(_CONSTRAINT, "fotos", type_="unique")
