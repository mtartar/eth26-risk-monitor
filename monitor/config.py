"""Environment-driven app configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config the ingestion pipeline needs. More gets added per phase."""

    substreams_api_token: str | None = None
    substreams_endpoint: str = "mainnet.eth.streamingfast.io:443"
    cursor_db_path: str = "data/cursors.sqlite3"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = Settings()
