import unittest
import uuid

from backend.jobs import JobRecord, JobWorker, utc_now_iso


class MemoryJobStore:
    def __init__(self) -> None:
        self.jobs: dict[str, JobRecord] = {}

    def create_job(self, job_type: str, params: dict | None = None) -> JobRecord:
        now = utc_now_iso()
        job = JobRecord(
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            type=job_type,
            status="pending",
            params=params or {},
        )
        self.jobs[job.id] = job
        return job

    def list_jobs(self, limit: int = 50) -> list[JobRecord]:
        return list(self.jobs.values())[:limit]

    def get_job(self, job_id: str) -> JobRecord | None:
        return self.jobs.get(job_id)

    def next_pending_job(self) -> JobRecord | None:
        return next((job for job in self.jobs.values() if job.status == "pending"), None)

    def update_job(
        self,
        job_id: str,
        *,
        status: str | None = None,
        result: dict | None = None,
        error: str | None = None,
        progress: float | None = None,
    ) -> JobRecord | None:
        current = self.jobs.get(job_id)
        if current is None:
            return None
        updated = JobRecord(
            id=current.id,
            created_at=current.created_at,
            updated_at=utc_now_iso(),
            type=current.type,
            status=status or current.status,
            params=current.params,
            result=result if result is not None else current.result,
            error=error if error is not None else current.error,
            progress=progress if progress is not None else current.progress,
        )
        self.jobs[job_id] = updated
        return updated

    def cancel_job(self, job_id: str) -> JobRecord | None:
        return self.update_job(job_id, status="canceled")

    def delete_job(self, job_id: str) -> bool:
        return self.jobs.pop(job_id, None) is not None


class JobStoreTests(unittest.TestCase):
    def test_job_lifecycle(self) -> None:
        store = MemoryJobStore()
        job = store.create_job("translation", {"text": "hello"})
        self.assertEqual(job.status, "pending")

        running = store.update_job(job.id, status="running", progress=0.5)
        self.assertIsNotNone(running)
        self.assertEqual(running.status, "running")
        self.assertEqual(running.progress, 0.5)

        completed = store.update_job(job.id, status="completed", result={"text": "xin chao"}, progress=1)
        self.assertIsNotNone(completed)
        self.assertEqual(completed.result, {"text": "xin chao"})
        self.assertEqual(store.list_jobs()[0].id, job.id)

    def test_cancel_pending_job(self) -> None:
        store = MemoryJobStore()
        job = store.create_job("translation", {"text": "hello"})
        canceled = store.cancel_job(job.id)
        self.assertIsNotNone(canceled)
        self.assertEqual(canceled.status, "canceled")

    def test_worker_runs_translation_job(self) -> None:
        store = MemoryJobStore()
        job = store.create_job(
            "translation",
            {
                "text": "hello",
                "source_language": "en",
                "target_language": "vi",
                "provider": "passthrough",
            },
        )
        worker = JobWorker(store=store)
        worker.run_job(job)
        completed = store.get_job(job.id)
        self.assertIsNotNone(completed)
        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.result["text"], "hello")


if __name__ == "__main__":
    unittest.main()
