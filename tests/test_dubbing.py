import unittest
import tempfile
from pathlib import Path

import numpy as np

from voicekit.dubbing import (
    fit_audio_to_duration,
    next_output_folder,
    normalize_speaker_voice_map,
    place_segment,
    sanitize_folder_name,
    voice_for_segment,
)


class DubbingAudioTests(unittest.TestCase):
    def test_fit_audio_truncates(self) -> None:
        audio = np.arange(10, dtype=np.float32)
        fitted = fit_audio_to_duration(audio, sample_rate=10, duration=0.5)
        self.assertEqual(fitted.tolist(), [0, 1, 2, 3, 4])

    def test_fit_audio_pads(self) -> None:
        audio = np.ones(3, dtype=np.float32)
        fitted = fit_audio_to_duration(audio, sample_rate=10, duration=0.5)
        self.assertEqual(fitted.size, 5)
        self.assertEqual(fitted[:3].tolist(), [1, 1, 1])
        self.assertEqual(fitted[3:].tolist(), [0, 0])

    def test_place_segment_adds_to_timeline(self) -> None:
        timeline = np.zeros(10, dtype=np.float32)
        place_segment(timeline, np.ones(3, dtype=np.float32), sample_rate=10, start=0.2, end=0.5)
        self.assertEqual(timeline.tolist(), [0, 0, 1, 1, 1, 0, 0, 0, 0, 0])

    def test_sanitize_folder_name(self) -> None:
        self.assertEqual(sanitize_folder_name("My Video!.mp4"), "My-Video-.mp4")
        self.assertEqual(sanitize_folder_name("   "), "dubbing")

    def test_next_output_folder_uses_incrementing_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first_name, first_path = next_output_folder(tmp, Path("My Video.mp4"))
            second_name, second_path = next_output_folder(tmp, Path("My Video.mp4"))
            custom_name, custom_path = next_output_folder(tmp, Path("ignored.mp4"), folder_name="Custom Name")
            self.assertEqual(first_name, "My-Video")
            self.assertEqual(second_name, "My-Video-2")
            self.assertEqual(custom_name, "Custom-Name")
            self.assertTrue(first_path.exists())
            self.assertTrue(second_path.exists())
            self.assertTrue(custom_path.exists())

    def test_voice_for_segment_uses_speaker_mapping(self) -> None:
        mapping = {"SPEAKER_00": "alice", "SPEAKER_01": "bob"}
        self.assertEqual(voice_for_segment("default", "SPEAKER_00", mapping), "alice")
        self.assertEqual(voice_for_segment("default", "SPEAKER_02", mapping), "default")
        self.assertEqual(voice_for_segment("default", None, mapping), "default")

    def test_normalize_speaker_voice_map_strips_empty_values(self) -> None:
        self.assertEqual(
            normalize_speaker_voice_map({" SPEAKER_00 ": " alice ", "": "skip", "SPEAKER_01": ""}),
            {"SPEAKER_00": "alice"},
        )


if __name__ == "__main__":
    unittest.main()
