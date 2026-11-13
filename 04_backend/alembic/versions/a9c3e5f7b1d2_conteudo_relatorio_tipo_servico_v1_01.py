"""conteudo_relatorio_tipo_servico_v1_01

V1-01 (fundação de dados da emissão dos 5 relatórios):
- normaliza `contratos.tipo_servico` e `inspecoes.tipo` para maiúsculas (havia
  valores como 'ltip'); o enum `TipoServico` passa a validar a entrada nos schemas;
- cria `relatorio_conteudos` (textos narrativos e dados editoriais por inspeção e
  tipo de relatório, UNIQUE(inspecao_id, tipo));
- adiciona `titulo_profissional`, `qualificacoes` (JSONB) e
  `assinatura_storage_key` em `responsaveis` (bloco de assinatura dos laudos).

O downgrade remove a tabela e as colunas, mas NÃO desfaz o upper(): a caixa
original não é recuperável e maiúsculas são válidas no esquema anterior.

Revision ID: a9c3e5f7b1d2
Revises: e5a1c7d9b3f4
Create Date: 2026-11-11 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9c3e5f7b1d2"
down_revision: str | Sequence[str] | None = "e5a1c7d9b3f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE contratos SET tipo_servico = upper(btrim(tipo_servico)) WHERE tipo_servico <> upper(btrim(tipo_servico))")
    op.execute("UPDATE inspecoes SET tipo = upper(btrim(tipo)) WHERE tipo <> upper(btrim(tipo))")

    op.create_table(
        "relatorio_conteudos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("inspecao_id", sa.UUID(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column(
            "dados",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("atualizado_por_id", sa.UUID(), nullable=True),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["inspecao_id"], ["inspecoes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["atualizado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inspecao_id", "tipo", name="uq_relatorio_conteudos_inspecao_tipo"),
    )

    op.add_column("responsaveis", sa.Column("titulo_profissional", sa.String(), nullable=True))
    op.add_column("responsaveis", sa.Column("qualificacoes", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("responsaveis", sa.Column("assinatura_storage_key", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("responsaveis", "assinatura_storage_key")
    op.drop_column("responsaveis", "qualificacoes")
    op.drop_column("responsaveis", "titulo_profissional")
    op.drop_table("relatorio_conteudos")
    # O upper() de contratos.tipo_servico / inspecoes.tipo não é revertido (ver docstring).
