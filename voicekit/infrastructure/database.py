import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DATABASE_ENV_KEYS = ("VOICEKIT_DATABASE_URL", "SUPABASE_DATABASE_URL", "DATABASE_URL")
_ENV_LOADED = False


def database_url() -> str:
    load_env_file()
    for key in DATABASE_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            return validate_database_url(value)
    raise RuntimeError(
        "PostgreSQL database URL is required. Set VOICEKIT_DATABASE_URL, SUPABASE_DATABASE_URL, or DATABASE_URL."
    )


def validate_database_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise RuntimeError("PostgreSQL database URL must start with postgresql:// or postgres://.")
    if not parsed.hostname or parsed.hostname == "postgres":
        raise RuntimeError(
            "PostgreSQL database URL host is invalid. If your password contains '/', '@', '#', '?', '&', ':', "
            "or '%', URL-encode the password before putting it in VOICEKIT_DATABASE_URL."
        )
    return value


def load_env_file() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    for path in _env_candidates():
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            key, value = _parse_env_line(line)
            if key and key not in os.environ:
                os.environ[key] = value


def _env_candidates() -> list[Path]:
    cwd = Path.cwd() / ".env"
    repo_root = Path(__file__).resolve().parents[1] / ".env"
    candidates = [cwd, repo_root]
    unique: list[Path] = []
    for path in candidates:
        if path not in unique:
            unique.append(path)
    return unique


def _parse_env_line(line: str) -> tuple[str | None, str]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None, ""
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()
    if value and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


@contextmanager
def postgres_connection():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as e:
        raise RuntimeError("Missing dependency 'psycopg'. Run `uv sync` before starting the API.") from e

    conn = psycopg.connect(database_url(), row_factory=dict_row, connect_timeout=10)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    return value


def iso_value(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
