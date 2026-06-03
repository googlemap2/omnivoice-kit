from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from voicekit.database import iso_value, json_value, postgres_connection


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ProviderModelRecord:
    id: str
    created_at: str
    updated_at: str
    provider_name: str
    provider_type: str
    base_url: str
    api_key: str | None = None
    speech_model: str | None = None
    transcription_model: str | None = None
    config: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProviderModelStore:
    table_name = "provider_models"

    def _ensure_table(self, conn) -> None:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                provider_name TEXT NOT NULL,
                provider_type TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key TEXT,
                speech_model TEXT,
                transcription_model TEXT,
                config JSONB NOT NULL DEFAULT '{{}}'::jsonb
            )
            """
        )
        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_name}_updated
            ON {self.table_name} (updated_at DESC)
            """
        )

    def upsert_cloud_provider(self, config: dict[str, Any] | None) -> ProviderModelRecord | None:
        from psycopg.types.json import Jsonb

        cloud = config if isinstance(config, dict) else {}
        base_url = str(cloud.get("base_url") or "").strip()

        now = utc_now_iso()
        record = ProviderModelRecord(
            id="cloud",
            created_at=now,
            updated_at=now,
            provider_name=str(cloud.get("provider_name") or "OpenAI-compatible Cloud").strip()
            or "OpenAI-compatible Cloud",
            provider_type="openai-compatible",
            base_url=base_url,
            api_key=str(cloud.get("api_key") or "").strip() or None,
            speech_model=str(cloud.get("speech_model") or "").strip() or None,
            transcription_model=str(cloud.get("transcription_model") or "").strip() or None,
            config={k: v for k, v in cloud.items() if k not in {"provider_name", "base_url", "api_key", "speech_model", "transcription_model"}},
        )
        with postgres_connection() as conn:
            self._ensure_table(conn)
            conn.execute(
                f"""
                INSERT INTO {self.table_name} (
                    id, created_at, updated_at, provider_name, provider_type, base_url,
                    api_key, speech_model, transcription_model, config
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    updated_at = EXCLUDED.updated_at,
                    provider_name = EXCLUDED.provider_name,
                    provider_type = EXCLUDED.provider_type,
                    base_url = EXCLUDED.base_url,
                    api_key = EXCLUDED.api_key,
                    speech_model = EXCLUDED.speech_model,
                    transcription_model = EXCLUDED.transcription_model,
                    config = EXCLUDED.config
                """,
                (
                    record.id,
                    record.created_at,
                    record.updated_at,
                    record.provider_name,
                    record.provider_type,
                    record.base_url,
                    record.api_key,
                    record.speech_model,
                    record.transcription_model,
                    Jsonb(record.config or {}),
                ),
            )
        return record

    def get_cloud_provider(self) -> ProviderModelRecord | None:
        with postgres_connection() as conn:
            self._ensure_table(conn)
            row = conn.execute(
                f"""
                SELECT id, created_at, updated_at, provider_name, provider_type, base_url,
                       api_key, speech_model, transcription_model, config
                FROM {self.table_name}
                WHERE id = %s
                """,
                ("cloud",),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    @staticmethod
    def _row_to_record(row: dict[str, Any]) -> ProviderModelRecord:
        return ProviderModelRecord(
            id=row["id"],
            created_at=iso_value(row["created_at"]),
            updated_at=iso_value(row["updated_at"]),
            provider_name=row["provider_name"],
            provider_type=row["provider_type"],
            base_url=row["base_url"],
            api_key=row["api_key"],
            speech_model=row["speech_model"],
            transcription_model=row["transcription_model"],
            config=json_value(row.get("config"), {}),
        )


def get_provider_model_store() -> ProviderModelStore:
    return ProviderModelStore()


def cloud_provider_to_settings_config(record: ProviderModelRecord) -> dict[str, Any]:
    return {
        **(record.config or {}),
        "provider_name": record.provider_name,
        "base_url": record.base_url,
        "api_key": record.api_key or "",
        "speech_model": record.speech_model or "",
        "transcription_model": record.transcription_model or "",
    }
