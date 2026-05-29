import os
from contextlib import contextmanager
from typing import Any


DATABASE_ENV_KEYS = ("VOICEKIT_DATABASE_URL", "SUPABASE_DATABASE_URL", "DATABASE_URL")


def database_url() -> str:
    for key in DATABASE_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            return value
    raise RuntimeError(
        "PostgreSQL database URL is required. Set VOICEKIT_DATABASE_URL, SUPABASE_DATABASE_URL, or DATABASE_URL."
    )


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
