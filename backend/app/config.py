import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://portal:portal@localhost:5432/portal"
    jwt_secret: str = "dev-only-change-me"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    # Comma-separated list of allowed frontend origins
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sqlalchemy_url(self) -> str:
        # Neon/Render hand out plain postgres:// URLs; point them at the psycopg v3 driver.
        url = self.database_url
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url


settings = Settings()
