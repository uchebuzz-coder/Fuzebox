"""Dashboard configuration from environment variables."""

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def get_dashboard_db_path() -> Path:
    """Resolve the SQLite database file path.

    If ``DASHBOARD_DB_PATH`` is set, it is interpreted as an absolute path or
    relative to the current working directory, then expanded and resolved.

    Otherwise the default is ``<repo root>/data/agent_dashboard.db``.
    """
    override = os.environ.get("DASHBOARD_DB_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return _REPO_ROOT / "data" / "agent_dashboard.db"
