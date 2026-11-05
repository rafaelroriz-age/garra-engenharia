"""legendas_ia_prompts_ia_bl_36

BL-36 / DEC-37 (proposta de T14) / ADR-12: persistência do fluxo de legendas assistidas por IA
(RF-15, RN-16, RN-17). Só modelo de dados: não há adapter de LLM nem endpoint de geração aqui.

- Cria `prompts_ia` (prompt-sistema versionado): `nome`, `versao`, `conteudo`, `ativo`,
  `created_at`, `criado_por_id`. `UNIQUE(nome, versao)` e índice único parcial
  `(nome) WHERE ativo` — no máximo uma versão ativa por nome (DEC-21, L19).
- Adiciona em `fotos`, todas anuláveis e sem default (linhas existentes ficam com NULL =
  "sem sugestão de IA"; nada é reescrito):
  `legenda_bruta`, `legenda_ia_sugerida` (minuta; `legenda` continua sendo a legenda final),
  `nivel_certeza_ia`, `status_validacao_ia` (`rascunho` | `aprovada`), `alertas_ia`,
  `pendencias_ia` (JSONB), `prompt_ia_id` (FK RESTRICT), `prompt_conteudo_hash` (SHA-256),
  `legenda_ia_gerada_em`, `aprovado_por_id` (FK `usuarios`), `aprovado_em`.
- CHECKs de domínio e de coerência (status exige sugestão; `aprovada` exige quem e quando).

`downgrade()` remove constraints, colunas e a tabela, na ordem inversa. Como as colunas são
novas, nenhum dado anterior a esta revisão é perdido; o que for gravado nelas é descartado.

Revision ID: f7c2a9d4e6b1
Revises: e5a1c3f7b9d2
Create Date: 2026-11-04 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7c2a9d4e6b1"
down_revision: str | Sequence[str] | None = "e5a1c3f7b9d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATUS_VALIDACAO = ("rascunho", "aprovada")
NIVEIS_CERTEZA = ("constatacao_direta", "indicio_tecnico", "hipotese_tecnica", "causa_comprovada")


def _in(coluna: str, valores: tuple[str, ...]) -> str:
    lista = ", ".join(f"'{v}'" for v in valores)
    return f"{coluna} IS NULL OR {coluna} IN ({lista})"


CHECKS_FOTOS = {
    "ck_fotos_status_validacao_ia": _in("status_validacao_ia", STATUS_VALIDACAO),
    "ck_fotos_nivel_certeza_ia": _in("nivel_certeza_ia", NIVEIS_CERTEZA),
    "ck_fotos_status_ia_exige_sugestao": "status_validacao_ia IS NULL OR legenda_ia_sugerida IS NOT NULL",
    "ck_fotos_aprovada_exige_aprovador": (
        "status_validacao_ia IS DISTINCT FROM 'aprovada' "
        "OR (aprovado_por_id IS NOT NULL AND aprovado_em IS NOT NULL)"
    ),
    "ck_fotos_prompt_conteudo_hash": "prompt_conteudo_hash IS NULL OR prompt_conteudo_hash ~ '^[0-9a-f]{64}$'",
}

COLUNAS_FOTOS = (
    "aprovado_em",
    "aprovado_por_id",
    "legenda_ia_gerada_em",
    "prompt_conteudo_hash",
    "prompt_ia_id",
    "pendencias_ia",
    "alertas_ia",
    "status_validacao_ia",
    "nivel_certeza_ia",
    "legenda_ia_sugerida",
    "legenda_bruta",
)


def upgrade() -> None:
    op.create_table(
        "prompts_ia",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("versao", sa.String(length=50), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("criado_por_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["criado_por_id"], ["usuarios.id"], name="fk_prompts_ia_criado_por_id_usuarios"),
        sa.PrimaryKeyConstraint("id", name="pk_prompts_ia"),
        sa.UniqueConstraint("nome", "versao", name="uq_prompts_ia_nome_versao"),
    )
    op.create_index(
        "uq_prompts_ia_nome_ativo",
        "prompts_ia",
        ["nome"],
        unique=True,
        postgresql_where=sa.text("ativo"),
    )

    op.add_column("fotos", sa.Column("legenda_bruta", sa.Text(), nullable=True))
    op.add_column("fotos", sa.Column("legenda_ia_sugerida", sa.Text(), nullable=True))
    op.add_column("fotos", sa.Column("nivel_certeza_ia", sa.String(length=30), nullable=True))
    op.add_column("fotos", sa.Column("status_validacao_ia", sa.String(length=20), nullable=True))
    op.add_column("fotos", sa.Column("alertas_ia", postgresql.JSONB(), nullable=True))
    op.add_column("fotos", sa.Column("pendencias_ia", postgresql.JSONB(), nullable=True))
    op.add_column("fotos", sa.Column("prompt_ia_id", sa.UUID(), nullable=True))
    op.add_column("fotos", sa.Column("prompt_conteudo_hash", sa.String(length=64), nullable=True))
    op.add_column("fotos", sa.Column("legenda_ia_gerada_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("fotos", sa.Column("aprovado_por_id", sa.UUID(), nullable=True))
    op.add_column("fotos", sa.Column("aprovado_em", sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key(
        "fk_fotos_prompt_ia_id_prompts_ia", "fotos", "prompts_ia", ["prompt_ia_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_foreign_key("fk_fotos_aprovado_por_id_usuarios", "fotos", "usuarios", ["aprovado_por_id"], ["id"])
    op.create_index("ix_fotos_prompt_ia_id", "fotos", ["prompt_ia_id"])
    for nome, condicao in CHECKS_FOTOS.items():
        op.create_check_constraint(nome, "fotos", condicao)


def downgrade() -> None:
    for nome in reversed(CHECKS_FOTOS):
        op.drop_constraint(nome, "fotos", type_="check")
    op.drop_index("ix_fotos_prompt_ia_id", table_name="fotos")
    op.drop_constraint("fk_fotos_aprovado_por_id_usuarios", "fotos", type_="foreignkey")
    op.drop_constraint("fk_fotos_prompt_ia_id_prompts_ia", "fotos", type_="foreignkey")
    for coluna in COLUNAS_FOTOS:
        op.drop_column("fotos", coluna)

    op.drop_index("uq_prompts_ia_nome_ativo", table_name="prompts_ia", postgresql_where=sa.text("ativo"))
    op.drop_table("prompts_ia")
