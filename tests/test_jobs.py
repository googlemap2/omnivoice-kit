import tempfile
import unittest
from pathlib import Path

from voicekit.jobs import JobStore, JobWorker


class JobStoreTests(unittest.TestCase):
    def test_job_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.sqlite3")
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
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.sqlite3")
            job = store.create_job("translation", {"text": "hello"})
            canceled = store.cancel_job(job.id)
            self.assertIsNotNone(canceled)
            self.assertEqual(canceled.status, "canceled")

    def test_worker_runs_translation_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore(Path(tmp) / "jobs.sqlite3")
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
