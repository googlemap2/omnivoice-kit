from __future__ import annotations

import logging
import platform
import re
import shutil
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from backend.infrastructure.media import check_ffmpeg, ffprobe_path
from backend.paths import DATA_DIR
from backend.infrastructure.model_store import DEFAULT_HF_CACHE, DEFAULT_MODEL_BASE_DIR, list_model_statuses


LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "backend.log"
_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)(\s*[=:]\s*)([^\s,'\"]+)"),
    re.compile(r"hf_[A-Za-z0-9_=-]{12,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
]


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact_text(super().format(record))


def redact_text(value: str) -> str:
    redacted = str(value)
    for pattern in _SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)"):
            redacted = pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def setup_logging(log_file: str | Path = LOG_FILE) -> logging.Logger:
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("backend")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    resolved = str(path.resolve())
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler) and getattr(handler, "baseFilename", None) == resolved:
            return logger
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(RedactingFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(handler)
    return logger


def read_logs(limit: int = 300, log_file: str | Path = LOG_FILE) -> list[str]:
    path = Path(log_file)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return [redact_text(line) for line in lines[-max(1, int(limit)) :]]


def clear_logs(log_file: str | Path = LOG_FILE) -> None:
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _torch_info() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    cuda_available = bool(torch.cuda.is_available())
    mps = getattr(torch.backends, "mps", None)
    mps_available = bool(mps and mps.is_available())
    return {
        "available": True,
        "version": getattr(torch, "__version__", None),
        "cuda_available": cuda_available,
        "cuda_device_count": int(torch.cuda.device_count()) if cuda_available else 0,
        "mps_available": mps_available,
    }


def _dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return total


def diagnostics_snapshot() -> dict[str, Any]:
    ffmpeg_available, ffmpeg_detail = check_ffmpeg()
    statuses = [status.to_dict() for status in list_model_statuses()]
    return {
        "system": {
            "platform": platform.platform(),
            "os": platform.system(),
            "python": sys.version.split()[0],
            "executable": sys.executable,
        },
        "device": _torch_info(),
        "ffmpeg": {
            "available": ffmpeg_available,
            "path": ffmpeg_detail if ffmpeg_available else None,
            "message": None if ffmpeg_available else ffmpeg_detail,
            "ffprobe_path": ffprobe_path(),
        },
        "models": {
            "base_dir": str(DEFAULT_MODEL_BASE_DIR.resolve()),
            "cache_dir": str(DEFAULT_HF_CACHE.resolve()),
            "base_dir_exists": DEFAULT_MODEL_BASE_DIR.exists(),
            "cache_dir_exists": DEFAULT_HF_CACHE.exists(),
            "cache_size_bytes": _dir_size(DEFAULT_MODEL_BASE_DIR),
            "installed_count": sum(1 for status in statuses if status.get("installed")),
            "statuses": statuses,
        },
        "logs": {
            "path": str(LOG_FILE.resolve()),
            "exists": LOG_FILE.exists(),
        },
    }
