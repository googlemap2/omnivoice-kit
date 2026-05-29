import unittest

import numpy as np

from voicekit.dubbing import fit_audio_to_duration, place_segment


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


if __name__ == "__main__":
    unittest.main()
