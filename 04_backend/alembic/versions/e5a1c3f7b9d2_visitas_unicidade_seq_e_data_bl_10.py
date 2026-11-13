"""visitas_unicidade_seq_e_data_bl_10

RN-01/DEC-38 (B): `seq_numero` único por inspeção e uma visita por dia de obra.
Cria `UNIQUE(inspecao_id, seq_numero)` e `UNIQUE(inspecao_id, data)` em `visitas`.
Não toca em nenhuma outra tabela (fotos, ocorrências etc. ficam intactas).

Tratamento de dados existentes (nada é apagado):

- `seq_numero` duplicado na mesma inspeção: em cada grupo (inspecao_id, seq_numero) fica com o
  número a visita de menor (data, id); as demais recebem `max(seq_numero) + n` da inspeção, na
  ordem (seq_numero, data, id). É determinístico e não altera nenhum número que já era único.
- `data` duplicada na mesma inspeção: não há correção automática segura (juntar ou mover a visita
  exige decisão humana, e há fotos vinculadas). A migration ABORTA com a lista dos pares
  duplicados, sem alterar nada (DDL transacional no PostgreSQL); corrija os dados e rode de novo.

`downgrade()` remove as duas constraints; a renumeração não é desfeita (os números duplicados
originais eram inválidos e não são guardados).

Revision ID: e5a1c3f7b9d2
Revises: d3b7c9e4f1a2
Create Date: 2026-11-04 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5a1c3f7b9d2"
down_revision: str | Sequence[str] | None = "d3b7c9e4f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UQ_SEQ = "uq_visitas_inspecao_id_seq_numero"
UQ_DATA = "uq_visitas_inspecao_id_data"

_DATAS_DUPLICADAS = sa.text(
    """
    SELECT inspecao_id, data, COUNT(*) AS qtd
    FROM visitas
    GROUP BY inspecao_id, data
    HAVING COUNT(*) > 1
    ORDER BY inspecao_id, data
    """
)

_RENUMERAR_SEQ_DUPLICADO = sa.text(
    """
    WITH grupos AS (
        SELECT id, inspecao_id, seq_numero, data,
               ROW_NUMBER() OVER (PARTITION BY inspecao_id, seq_numero ORDER BY data, id) AS pos_grupo
        FROM visitas
    ),
    extras AS (
        SELECT id, inspecao_id,
               ROW_NUMBER() OVER (PARTITION BY inspecao_id ORDER BY seq_numero, data, id) AS ordem
        FROM grupos
        WHERE pos_grupo > 1
    ),
    maiores AS (
        SELECT inspecao_id, MAX(seq_numero) AS maior FROM visitas GROUP BY inspecao_id
    )
    UPDATE visitas AS v
    SET seq_numero = m.maior + e.ordem
    FROM extras AS e
    JOIN maiores AS m ON m.inspecao_id = e.inspecao_id
    WHERE v.id = e.id
    """
)


def upgrade() -> None:
    bind = op.get_bind()

    duplicadas = bind.execute(_DATAS_DUPLICADAS).all()
    if duplicadas:
        lista = "; ".join(f"inspecao_id={r.inspecao_id} data={r.data} ({r.qtd} visitas)" for r in duplicadas)
        raise RuntimeError(
            "Há visitas na mesma data dentro de uma inspeção (RN-01: uma por dia). Corrija manualmente "
            f"(mover a data ou unir as visitas) antes de aplicar {UQ_DATA}: {lista}"
        )

    renumeradas = bind.execute(_RENUMERAR_SEQ_DUPLICADO).rowcount
    if renumeradas:
        print(f"[e5a1c3f7b9d2] {renumeradas} visita(s) com seq_numero duplicado renumerada(s).")

    op.create_unique_constraint(UQ_SEQ, "visitas", ["inspecao_id", "seq_numero"])
    op.create_unique_constraint(UQ_DATA, "visitas", ["inspecao_id", "data"])


def downgrade() -> None:
    op.drop_constraint(UQ_DATA, "visitas", type_="unique")
    op.drop_constraint(UQ_SEQ, "visitas", type_="unique")
