import unittest

from voicekit.diarization import DiarizationSegment, assign_speakers_to_segments, overlap_seconds


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


if __name__ == "__main__":
    unittest.main()
