"""Environment-driven app configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict

# Reuses the already-verified working Anthropic key from the sibling
# eth26-graph-trail project during local dev, so Phase 3 doesn't need a
# second key generated/configured for the same account. Loaded first so this
# repo's own .env (if it sets ANTHROPIC_API_KEY itself) still takes
# precedence. A missing file here is not an error — pydantic-settings skips
# it silently — so this stays harmless on any machine that doesn't have that
# sibling repo checked out.
_GRAPH_TRAIL_ENV = "/home/numrise/eth26-graph-trail/.env"


class Settings(BaseSettings):
    """Config the ingestion pipeline and AI layer need. More gets added per phase."""

    substreams_api_token: str | None = None
    substreams_endpoint: str = "mainnet.eth.streamingfast.io:443"
    cursor_db_path: str = "data/cursors.sqlite3"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-haiku-4-5-20251001"

    model_config = SettingsConfigDict(
        env_file=(_GRAPH_TRAIL_ENV, ".env"),
        env_prefix="",
        extra="ignore",
    )


settings = Settings()
