from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_path: str = "./leadpilot.db"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    company_name: str = "LeadPilot Demo"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
