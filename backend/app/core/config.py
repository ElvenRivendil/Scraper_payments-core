from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "payments-core"
    helm_auth_base_url: str = "http://host.docker.internal:8001"
    helm_internal_api_secret: str = ""
    app_env: str = "development"
    database_url: str = Field(default="")
    redis_url: str = Field(default="redis://localhost:6379/0")
    demo_secret: str = Field(default="change-me")
    scripe_provisioning_secret: str = ""
    demo_endpoints_enabled: bool = False
    demo_reset_enabled: bool = False
    demo_reset_database_url: str = ""
    public_demo: bool = False
    auto_seed: bool = True
    auto_seed_on_empty: bool = False
    enqueue_webhooks: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost:5174"])


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
