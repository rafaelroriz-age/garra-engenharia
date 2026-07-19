"""Configurações da aplicação, carregadas de variáveis de ambiente / `.env`.

Ver DEC-05 (`00_docs/projeto/decisoes.md`) e Seção 7 de `00_docs/arquitetura.md`.
Em desenvolvimento local (fora de Docker), copie `04_backend/.env.example` para
`04_backend/.env`. Ao rodar via `docker compose` (05_infra/), as variáveis são
injetadas diretamente pelo serviço `backend` e este arquivo `.env` não é necessário.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação lidas do ambiente (case-insensitive)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Aplicação -----------------------------------------------------------
    app_name: str = "Sistema de Automação de Relatórios Prediais"
    environment: str = "development"
    backend_cors_origins: str = "http://localhost:3000"

    # --- PostgreSQL (DEC-07) ---------------------------------------------------
    postgres_user: str = "garra"
    postgres_password: str = ""
    postgres_db: str = "garra_engenharia"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # --- MinIO (DEC-02) ---------------------------------------------------------
    minio_root_user: str = ""
    minio_root_password: str = ""
    minio_bucket_name: str = "relatorios-prediais"
    minio_host: str = "localhost"
    minio_api_port: int = 9000
    minio_use_ssl: bool = False

    # --- JWT (RNF-05, DEC-05) ----------------------------------------------------
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    @property
    def database_url(self) -> str:
        """URL de conexão assíncrona do SQLAlchemy (driver `asyncpg`)."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def minio_endpoint_url(self) -> str:
        """URL completa (com esquema) do endpoint S3-compatível do MinIO."""
        scheme = "https" if self.minio_use_ssl else "http"
        return f"{scheme}://{self.minio_host}:{self.minio_api_port}"

    @property
    def cors_origins_list(self) -> list[str]:
        """Lista de origens permitidas para CORS a partir da string separada por vírgulas."""
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância cacheada de `Settings` (evita reparsing repetido do ambiente)."""
    return Settings()
