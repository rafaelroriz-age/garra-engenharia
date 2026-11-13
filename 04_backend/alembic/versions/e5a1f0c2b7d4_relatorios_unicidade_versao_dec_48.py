"""relatorios_unicidade_versao_dec_48

DEC-48 P3: a emissão do RFO cria um `Relatorio` novo por emissão (V01, V02...).
Até aqui a unicidade de (inspecao_id, tipo, versao) dependia só do lock
`FOR NO KEY UPDATE`; esta migration a garante no banco.

O upgrade NÃO apaga nem renumera dados: se houver duplicatas, aborta listando-as
para limpeza manual.

Revision ID: e5a1f0c2b7d4
Revises: d3b7c9e4f1a2
Create Date: 2026-11-10 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e5a1f0c2b7d4"
down_revision: str | Sequence[str] | None = "d3b7c9e4f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT = "uq_relatorios_inspecao_tipo_versao"


def upgrade() -> None:
    bind = op.get_bind()
    dups = bind.execute(
        sa.text(
            "SELECT inspecao_id, tipo, versao, count(*) AS n, array_agg(id::text ORDER BY id) AS ids "
            "FROM relatorios GROUP BY inspecao_id, tipo, versao HAVING count(*) > 1"
        )
    ).fetchall()
    if dups:
        linhas = "\n".join(
            f"  inspecao_id={d.inspecao_id} tipo={d.tipo} versao={d.versao} "
            f"({d.n} registros: {', '.join(d.ids)})"
            for d in dups
        )
        raise RuntimeError(
            f"Existem {len(dups)} grupo(s) duplicado(s) em relatorios "
            f"(inspecao_id, tipo, versao); a constraint {CONSTRAINT} não pode ser criada.\n"
            f"{linhas}\n"
            "Limpe manualmente (revise e remova/renumere com critério de negócio) e rode "
            "o upgrade novamente. Esta migration não altera dados."
        )
    op.create_unique_constraint(CONSTRAINT, "relatorios", ["inspecao_id", "tipo", "versao"])


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT, "relatorios", type_="unique")
