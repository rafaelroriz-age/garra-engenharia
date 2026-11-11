"""Configurações da aplicação, carregadas de variáveis de ambiente / `.env`.

Ver DEC-05 (`00_docs/projeto/decisoes.md`) e Seção 7 de `00_docs/arquitetura.md`.
Em desenvolvimento local (fora de Docker), copie `04_backend/.env.example` para
`04_backend/.env`. Ao rodar via `docker compose` (05_infra/), as variáveis são
injetadas diretamente pelo serviço `backend` e este arquivo `.env` não é necessário.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação lidas do ambiente (case-insensitive)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Aplicação -----------------------------------------------------------
    app_name: str = "Sistema de Automação de Relatórios Prediais"
    environment: str = "development"
    backend_cors_origins: str = "http://localhost:3000"
    # Para plataformas sem Pre-Deploy Command (Render, runtime nativo): aplica
    # `alembic upgrade head` no boot. Ver `app/core/migrations.py`.
    run_migrations_on_startup: bool = False

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

    # --- Legenda por IA: limites de geração e da saída do LLM (DEC-42 C) ----------
    legenda_ia_limite_por_usuario: int = Field(default=10, ge=1)
    legenda_ia_janela_usuario_segundos: int = Field(default=60, ge=1)
    legenda_ia_limite_diario_por_usuario: int = Field(default=200, ge=1)
    legenda_ia_limite_por_foto: int = Field(default=5, ge=1)
    legenda_ia_janela_foto_segundos: int = Field(default=3600, ge=1)
    # Até 500: a sugestão aprovada vira `legenda`, cujo teto é LEGENDA_MAX_LENGTH (schemas/foto.py).
    legenda_ia_saida_max_caracteres: int = Field(default=500, ge=1, le=500)
    legenda_ia_saida_max_itens: int = Field(default=20, ge=1)
    legenda_ia_saida_max_caracteres_item: int = Field(default=300, ge=1)

    # --- Legenda por IA: provedor (B-04 decidido: DeepSeek Platform API, V1-07) -----
    legenda_ia_provedor: Literal["fake", "deepseek"] = "fake"
    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_modelo: str = "deepseek-flash"
    deepseek_timeout_s: float = Field(default=30.0, gt=0)
    # A doc oficial não confirma modelo com visão: por padrão só texto (modo='texto').
    deepseek_enviar_imagem: bool = False

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

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in {"development", "dev", "local", "test"}

    @model_validator(mode="after")
    def _validar_segredos_de_producao(self) -> "Settings":
        """Fail-closed (OWASP A05, BL-23): impede subir produção com segredo default."""
        if not self.is_development:
            if self.jwt_secret_key in {"", "changeme"} or len(self.jwt_secret_key) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY ausente, default ou curta demais para ENVIRONMENT="
                    f"'{self.environment}'. Defina um valor aleatório de pelo menos 32 caracteres."
                )
            if "*" in self.cors_origins_list:
                raise ValueError("BACKEND_CORS_ORIGINS não pode ser '*' fora de desenvolvimento.")
            chave = self.deepseek_api_key.get_secret_value().strip() if self.deepseek_api_key else ""
            if self.legenda_ia_provedor == "deepseek" and not chave:
                raise ValueError(
                    "LEGENDA_IA_PROVEDOR=deepseek exige DEEPSEEK_API_KEY em ENVIRONMENT="
                    f"'{self.environment}'. Defina a chave ou use LEGENDA_IA_PROVEDOR=fake."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância cacheada de `Settings` (evita reparsing repetido do ambiente)."""
    return Settings()
