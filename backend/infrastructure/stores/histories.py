import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from backend.infrastructure.database import iso_value, json_value, postgres_connection


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class GenerationHistoryEntry:
    id: str
    created_at: str
    mode: str
    model: str | None
    text: str
    voice: str | None = None
    language: str | None = None
    output_path: str | None = None
    params: dict[str, Any] | None = None
    status: str = "completed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GenerationHistoryStore:
    table_name = "histories"

    def _ensure_table(self, conn) -> None:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                mode TEXT NOT NULL,
                model TEXT,
                text TEXT NOT NULL,
                voice TEXT,
                language TEXT,
                output_path TEXT,
                params JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                status TEXT NOT NULL
            )
            """
        )
        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created
            ON {self.table_name} (created_at DESC)
            """
        )

    def record_generation(
        self,
        mode: str,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        language: str | None = None,
        output_path: str | None = None,
        params: dict[str, Any] | None = None,
        status: str = "completed",
    ) -> GenerationHistoryEntry:
        from psycopg.types.json import Jsonb

        entry = GenerationHistoryEntry(
            id=str(uuid.uuid4()),
            created_at=utc_now_iso(),
            mode=mode,
            model=model,
            text=text,
            voice=voice,
            language=language,
            output_path=output_path,
            params=params or {},
            status=status,
        )
        with postgres_connection() as conn:
            self._ensure_table(conn)
            conn.execute(
                f"""
                INSERT INTO {self.table_name} (
                    id, created_at, mode, model, text, voice, language, output_path, params, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry.id,
                    entry.created_at,
                    entry.mode,
                    entry.model,
                    entry.text,
                    entry.voice,
                    entry.language,
                    entry.output_path,
                    Jsonb(entry.params),
                    entry.status,
                ),
            )
        return entry

    def list_history(self, limit: int = 50) -> list[GenerationHistoryEntry]:
        with postgres_connection() as conn:
            self._ensure_table(conn)
            rows = conn.execute(
                f"""
                SELECT id, created_at, mode, model, text, voice, language, output_path, params, status
                FROM {self.table_name}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def get_history_entry(self, entry_id: str) -> GenerationHistoryEntry | None:
        with postgres_connection() as conn:
            self._ensure_table(conn)
            row = conn.execute(
                f"""
                SELECT id, created_at, mode, model, text, voice, language, output_path, params, status
                FROM {self.table_name}
                WHERE id = %s
                """,
                (entry_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_entry(row)

    @staticmethod
    def _row_to_entry(row: dict[str, Any]) -> GenerationHistoryEntry:
        return GenerationHistoryEntry(
            id=row["id"],
            created_at=iso_value(row["created_at"]),
            mode=row["mode"],
            model=row["model"],
            text=row["text"],
            voice=row["voice"],
            language=row["language"],
            output_path=row["output_path"],
            params=json_value(row.get("params"), {}),
            status=row["status"],
        )


def get_history_store() -> GenerationHistoryStore:
    return GenerationHistoryStore()


def record_generation(**kwargs) -> GenerationHistoryEntry:
    return get_history_store().record_generation(**kwargs)


def try_record_generation(**kwargs) -> GenerationHistoryEntry | None:
    try:
        return record_generation(**kwargs)
    except Exception:
        return None


def list_history(limit: int = 50) -> list[dict[str, Any]]:
    return [entry.to_dict() for entry in get_history_store().list_history(limit=limit)]
