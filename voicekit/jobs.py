import json
import sqlite3
import threading
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal


DEFAULT_JOBS_DB_PATH = Path("data") / "jobs.sqlite3"
JOB_STATUSES = ("pending", "running", "completed", "failed", "canceled")
JobStatus = Literal["pending", "running", "completed", "failed", "canceled"]
JobType = Literal["translation", "transcription", "dubbing", "speech"]


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class JobRecord:
    id: str
    created_at: str
    updated_at: str
    type: str
    status: str
    params: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None
    progress: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JobStore:
    def __init__(self, db_path: str | Path = DEFAULT_JOBS_DB_PATH):
        self.db_path = Path(db_path)

    @contextmanager
    def _connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    progress REAL NOT NULL DEFAULT 0
                )
                """
            )
            yield conn
            conn.commit()
        finally:
            conn.close()

    def create_job(self, job_type: str, params: dict[str, Any] | None = None) -> JobRecord:
        now = utc_now_iso()
        record = JobRecord(
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            type=job_type,
            status="pending",
            params=params or {},
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (id, created_at, updated_at, type, status, params_json, result_json, error, progress)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.created_at,
                    record.updated_at,
                    record.type,
                    record.status,
                    json.dumps(record.params, ensure_ascii=True),
                    None,
                    None,
                    record.progress,
                ),
            )
        return record

    def list_jobs(self, limit: int = 50) -> list[JobRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, updated_at, type, status, params_json, result_json, error, progress
                FROM jobs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, created_at, updated_at, type, status, params_json, result_json, error, progress
                FROM jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def next_pending_job(self) -> JobRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, created_at, updated_at, type, status, params_json, result_json, error, progress
                FROM jobs
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def update_job(
        self,
        job_id: str,
        *,
        status: str | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        progress: float | None = None,
    ) -> JobRecord | None:
        current = self.get_job(job_id)
        if current is None:
            return None
        next_status = status or current.status
        next_result = result if result is not None else current.result
        next_error = error if error is not None else current.error
        next_progress = progress if progress is not None else current.progress
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET updated_at = ?, status = ?, result_json = ?, error = ?, progress = ?
                WHERE id = ?
                """,
                (
                    utc_now_iso(),
                    next_status,
                    json.dumps(next_result, ensure_ascii=True) if next_result is not None else None,
                    next_error,
                    float(next_progress),
                    job_id,
                ),
            )
        return self.get_job(job_id)

    def cancel_job(self, job_id: str) -> JobRecord | None:
        current = self.get_job(job_id)
        if current is None:
            return None
        if current.status in {"completed", "failed", "canceled"}:
            return current
        return self.update_job(job_id, status="canceled", progress=current.progress)

    def delete_job(self, job_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            id=row["id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            type=row["type"],
            status=row["status"],
            params=_loads(row["params_json"], {}),
            result=_loads(row["result_json"], None),
            error=row["error"],
            progress=float(row["progress"] or 0),
        )


class JobWorker:
    def __init__(self, store: JobStore | None = None, poll_interval: float = 1.0):
        self.store = store or get_job_store()
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="voicekit-job-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            job = self.store.next_pending_job()
            if job is None:
                self._stop_event.wait(self.poll_interval)
                continue
            self.run_job(job)

    def run_job(self, job: JobRecord) -> JobRecord | None:
        current = self.store.get_job(job.id)
        if current is None or current.status == "canceled":
            return current
        self.store.update_job(job.id, status="running", progress=0.05)
        try:
            result = execute_job(job.type, job.params)
        except Exception as e:
            return self.store.update_job(
                job.id,
                status="failed",
                error=f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
                progress=1.0,
            )
        current = self.store.get_job(job.id)
        if current and current.status == "canceled":
            return current
        return self.store.update_job(job.id, status="completed", result=result, progress=1.0)


def execute_job(job_type: str, params: dict[str, Any]) -> dict[str, Any]:
    if job_type == "translation":
        from voicekit.translation import translate_segments, translate_text

        if params.get("segments"):
            result = translate_segments(
                segments=params["segments"],
                source_language=params.get("source_language"),
                target_language=params.get("target_language"),
                provider_id=params.get("provider"),
            )
        else:
            result = translate_text(
                text=str(params.get("text") or ""),
                source_language=params.get("source_language"),
                target_language=params.get("target_language"),
                provider_id=params.get("provider"),
            )
        return result.to_dict()

    if job_type == "transcription":
        from voicekit.asr import transcribe_file

        result = transcribe_file(**params)
        return result.to_dict(verbose=True)

    if job_type == "dubbing":
        from voicekit.dubbing import dub_file

        return dub_file(**params).to_dict()

    if job_type == "speech":
        import soundfile as sf

        from voicekit.core import generate_clone_with_speaker_id

        output_dir = Path(params.pop("output_dir", "outputs/jobs"))
        output_dir.mkdir(parents=True, exist_ok=True)
        audio, status = generate_clone_with_speaker_id(**params)
        if audio is None:
            raise RuntimeError(status)
        sample_rate, samples = audio
        output_path = output_dir / f"speech_{uuid.uuid4().hex}.wav"
        sf.write(output_path, samples, sample_rate, format="WAV", subtype="PCM_16")
        return {"status": status, "output_path": str(output_path)}

    raise ValueError(f"Unsupported job type: {job_type}")


def _loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def get_job_store() -> JobStore:
    return JobStore()


_worker = JobWorker()


def get_job_worker() -> JobWorker:
    return _worker
