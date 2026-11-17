"""POSTGRES_SSL e a URL de conexao (DEC-58, T87): Neon exige TLS; o Postgres de dev nao."""

from pathlib import Path

from app.core.config import Settings

BACKEND = Path(__file__).resolve().parents[1]


def _settings(**extra) -> Settings:
    return Settings(
        _env_file=None,
        postgres_user="u",
        postgres_password="p",
        postgres_db="d",
        postgres_host="db.exemplo.invalid",
        postgres_port=5432,
        **extra,
    )


def test_database_url_sem_tls_por_padrao():
    assert _settings().database_url == "postgresql+asyncpg://u:p@db.exemplo.invalid:5432/d"


def test_database_url_com_tls_acrescenta_ssl_require():
    url = _settings(postgres_ssl=True).database_url
    assert url == "postgresql+asyncpg://u:p@db.exemplo.invalid:5432/d?ssl=require"


def test_postgres_ssl_false_explicito_nao_acrescenta_nada():
    assert "ssl" not in _settings(postgres_ssl=False).database_url


def test_postgres_ssl_vem_da_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("POSTGRES_SSL", "true")
    assert Settings(_env_file=None).database_url.endswith("?ssl=require")


def test_alembic_e_boot_usam_a_mesma_database_url():
    # Uma unica fonte de verdade: ambos leem get_settings().database_url, entao herdam o TLS.
    for rel in ("alembic/env.py", "app/core/migrations.py"):
        texto = (BACKEND / rel).read_text(encoding="utf-8")
        assert 'set_main_option("sqlalchemy.url", get_settings().database_url)' in texto, rel
