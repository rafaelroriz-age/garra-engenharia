"""trechos_conhecimento_ia_rag_bl_34

BL-34 (IA-05, plano-deepseek item 6): RAG da legenda IA por busca textual do PostgreSQL
(FTS `portuguese` + `pg_trgm`), sem embeddings — a DeepSeek não tem API de embeddings.

- `CREATE EXTENSION IF NOT EXISTS pg_trgm`.
- Tabela `trechos_conhecimento_ia`: trechos anonimizados de relatórios históricos
  (`00_docs/convertidos/*.md`) e NBRs, com `tsv` gerada (`to_tsvector('portuguese', texto)`),
  índice GIN no `tsv` e GIN trigram no `texto`; `hash` único torna a ingestão idempotente.
- Índice GIN de expressão `to_tsvector('portuguese', legenda)` em `fotos`, só das legendas
  aprovadas (`status_validacao_ia = 'aprovada'`), usado para escolher os few-shots.

`downgrade()` remove índices e tabela. A extensão só é removida se foi esta migration que a
criou: o upgrade grava essa informação no comentário da tabela, lido no downgrade antes do DROP.

Revision ID: c6f2a8d4e1b9
Revises: b8d4f2a6c1e7
Create Date: 2026-11-12 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c6f2a8d4e1b9"
down_revision: str | Sequence[str] | None = "b8d4f2a6c1e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABELA = "trechos_conhecimento_ia"
_MARCA_EXTENSAO = "pg_trgm criada por c6f2a8d4e1b9"


def upgrade() -> None:
    bind = op.get_bind()
    ja_existia = bind.execute(sa.text("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")).scalar()
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        _TABELA,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fonte", sa.String(length=300), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("sistema", sa.String(length=120), nullable=True),
        sa.Column("tipo_anomalia", sa.String(length=120), nullable=True),
        sa.Column("grau_risco", sa.String(length=30), nullable=True),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column(
            "tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('portuguese'::regconfig, texto)", persisted=True),
            nullable=True,
        ),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hash", name="uq_trechos_conhecimento_ia_hash"),
        sa.CheckConstraint(
            "tipo IN ('relatorio_historico', 'nbr')", name="ck_trechos_conhecimento_ia_tipo"
        ),
    )
    op.create_index(
        "ix_trechos_conhecimento_ia_tsv", _TABELA, ["tsv"], postgresql_using="gin"
    )
    op.execute(
        f"CREATE INDEX ix_trechos_conhecimento_ia_texto_trgm ON {_TABELA} "
        "USING gin (texto gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_fotos_legenda_aprovada_fts ON fotos "
        "USING gin (to_tsvector('portuguese'::regconfig, legenda)) "
        "WHERE status_validacao_ia = 'aprovada'"
    )
    if not ja_existia:
        op.execute(f"COMMENT ON TABLE {_TABELA} IS '{_MARCA_EXTENSAO}'")


def downgrade() -> None:
    bind = op.get_bind()
    comentario = bind.execute(
        sa.text("SELECT obj_description(to_regclass(:t), 'pg_class')"), {"t": _TABELA}
    ).scalar()
    op.execute("DROP INDEX IF EXISTS ix_fotos_legenda_aprovada_fts")
    op.execute(f"DROP INDEX IF EXISTS ix_{_TABELA}_texto_trgm")
    op.drop_index("ix_trechos_conhecimento_ia_tsv", table_name=_TABELA)
    op.drop_table(_TABELA)
    if comentario == _MARCA_EXTENSAO:
        # RESTRICT (padrão): falha se outro objeto passou a depender da extensão depois do upgrade.
        op.execute("DROP EXTENSION IF EXISTS pg_trgm")
