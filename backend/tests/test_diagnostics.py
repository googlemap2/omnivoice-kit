import tempfile
import unittest
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.services.diagnostics_service import clear_logs, diagnostics_snapshot, read_logs, redact_text, setup_logging


class DiagnosticsTests(unittest.TestCase):
    def test_redact_text_masks_common_secret_shapes(self) -> None:
        text = "api_key=abc123 token: hf_abcdefghijklmnopqrstuvwxyz secret=sk-abcdefghijklmnop"
        redacted = redact_text(text)

        self.assertIn("api_key=[REDACTED]", redacted)
        self.assertIn("token: [REDACTED]", redacted)
        self.assertNotIn("abc123", redacted)
        self.assertNotIn("hf_abcdefghijklmnopqrstuvwxyz", redacted)

    def test_log_read_and_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "backend.log"
            logger = setup_logging(log_path)
            try:
                logger.info("token=secret-value")

                lines = read_logs(log_file=log_path)
                self.assertTrue(any("token=[REDACTED]" in line for line in lines))

                clear_logs(log_file=log_path)
                self.assertEqual(read_logs(log_file=log_path), [])
            finally:
                for handler in list(logger.handlers):
                    if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == log_path:
                        logger.removeHandler(handler)
                        handler.close()

    def test_diagnostics_snapshot_shape(self) -> None:
        snapshot = diagnostics_snapshot()

        self.assertIn("system", snapshot)
        self.assertIn("device", snapshot)
        self.assertIn("ffmpeg", snapshot)
        self.assertIn("models", snapshot)
        self.assertIn("logs", snapshot)


if __name__ == "__main__":
    unittest.main()
