from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KubeSight AI"
    app_version: str = "0.1.0"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    secret_key: SecretStr = Field(default=SecretStr("change-me"))
    access_token_expire_minutes: int = 60

    database_url: str = (
        "postgresql+psycopg://kubesight:kubesight@localhost:5432/kubesight"
    )

    kubeconfig_path: str | None = None
    kubernetes_context: str | None = None
    monitored_cluster_name: str = "local-cluster"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
