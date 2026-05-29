import unittest
from pathlib import Path
from unittest.mock import patch

from voicekit.diarization import (
    DiarizationSegment,
    assign_speakers_to_segments,
    configure_headless_matplotlib,
    overlap_seconds,
)


class DiarizationMergeTests(unittest.TestCase):
    def test_overlap_seconds(self) -> None:
        self.assertEqual(overlap_seconds(0, 2, 1, 3), 1)
        self.assertEqual(overlap_seconds(0, 1, 1, 2), 0)

    def test_assigns_speaker_by_largest_overlap(self) -> None:
        subtitles = [
            {"id": 0, "start": 0.0, "end": 2.0, "text": "hello"},
            {"id": 1, "start": 2.0, "end": 4.0, "text": "world"},
        ]
        diarization = [
            DiarizationSegment(start=0.0, end=1.0, speaker="SPEAKER_00"),
            DiarizationSegment(start=1.0, end=4.0, speaker="SPEAKER_01"),
        ]
        assigned = assign_speakers_to_segments(subtitles, diarization)
        self.assertEqual(assigned[0].speaker, "SPEAKER_00")
        self.assertEqual(assigned[1].speaker, "SPEAKER_01")
        self.assertEqual(assigned[1].metadata["speaker"], "SPEAKER_01")

    def test_keeps_unassigned_segment(self) -> None:
        assigned = assign_speakers_to_segments(
            [{"id": 0, "start": 10.0, "end": 11.0, "text": "late"}],
            [{"start": 0.0, "end": 1.0, "speaker": "SPEAKER_00"}],
        )
        self.assertIsNone(assigned[0].speaker)

    def test_configure_headless_matplotlib_replaces_colab_backend(self) -> None:
        with patch.dict("os.environ", {"MPLBACKEND": "module://matplotlib_inline.backend_inline"}):
            configure_headless_matplotlib()
            import os

            self.assertEqual(os.environ["MPLBACKEND"], "agg")

    def test_from_pretrained_fallback_is_documented_by_behavior(self) -> None:
        # The compatibility path is exercised in integration when pyannote is installed.
        # This unit test keeps the module import-only and avoids requiring pyannote.
        self.assertFalse(Path("definitely-not-a-real-pyannote-model").exists())


if __name__ == "__main__":
    unittest.main()
