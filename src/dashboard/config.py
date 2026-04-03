"""Dashboard configuration from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """All configuration read from environment variables with sensible defaults.

    Environment variables (all optional):
        DASHBOARD_DB_PATH   — absolute path to the SQLite database file
        AGENTS_CONFIG_DIR   — directory containing per-agent YAML files
        MARKET_CONFIG_DIR   — directory containing market config files (tickers.yaml)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    dashboard_db_path: Path = _REPO_ROOT / "data" / "agent_dashboard.db"
    agents_config_dir: Path = _REPO_ROOT / "agents"
    market_config_dir: Path = _REPO_ROOT / "config" / "market"


# Module-level singleton — import `settings` directly for new code.
settings = Settings()


def get_dashboard_db_path() -> Path:
    """Backwards-compatible accessor for the dashboard DB path.

    Existing callers (db.py) use this function; new code should read
    ``settings.dashboard_db_path`` directly.
    """
    return settings.dashboard_db_path
