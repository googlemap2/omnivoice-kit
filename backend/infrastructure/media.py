from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def ffmpeg_path() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError("ffmpeg is required for media processing but was not found in PATH.")
    return path


def ffprobe_path() -> str | None:
    return shutil.which("ffprobe")


def check_ffmpeg() -> tuple[bool, str | None]:
    path = shutil.which("ffmpeg")
    if not path:
        return False, "ffmpeg was not found in PATH."
    return True, path


def run_ffmpeg(args: list[str]) -> None:
    command = [ffmpeg_path(), "-y", *args]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"ffmpeg failed with exit code {result.returncode}: {detail}")


def extract_audio(input_path: str | Path, output_wav: str | Path, sample_rate: int = 16000) -> Path:
    output = Path(output_wav)
    output.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            str(output),
        ]
    )
    return output


def has_video_stream(input_path: str | Path) -> bool:
    probe = ffprobe_path()
    if not probe:
        return Path(input_path).suffix.lower() in {".mp4", ".mov", ".mkv", ".webm", ".avi"}
    result = subprocess.run(
        [
            probe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "csv=p=0",
            str(input_path),
        ],
        capture_output=True,
        text=True,
    )
    return "video" in (result.stdout or "").lower()


def mux_video_with_audio(input_video: str | Path, dubbed_wav: str | Path, output_video: str | Path) -> Path:
    output = Path(output_video)
    output.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-i",
            str(input_video),
            "-i",
            str(dubbed_wav),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(output),
        ]
    )
    return output
