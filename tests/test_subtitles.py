import unittest

from voicekit.subtitles import export_subtitle, parse_srt, parse_subtitle, parse_vtt


class SubtitleRoundtripTests(unittest.TestCase):
    def test_parse_srt(self) -> None:
        segments = parse_srt(
            "1\n"
            "00:00:01,000 --> 00:00:02,500\n"
            "Xin chao\n\n"
            "2\n"
            "00:00:03,000 --> 00:00:04,250\n"
            "the gioi\n"
        )
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].start, 1.0)
        self.assertEqual(segments[0].end, 2.5)
        self.assertEqual(segments[0].text, "Xin chao")

    def test_srt_roundtrip(self) -> None:
        source = (
            "1\n"
            "00:00:01,000 --> 00:00:02,500\n"
            "Xin chao\n\n"
            "2\n"
            "00:00:03,000 --> 00:00:04,250\n"
            "the gioi\n"
        )
        exported = export_subtitle(parse_srt(source), "srt")
        self.assertIn("00:00:01,000 --> 00:00:02,500", exported)
        self.assertIn("the gioi", exported)

    def test_parse_vtt(self) -> None:
        segments = parse_vtt(
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:02.500\n"
            "Hello\n\n"
            "cue-id\n"
            "00:00:03.000 --> 00:00:04.250\n"
            "world\n"
        )
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[1].text, "world")

    def test_vtt_roundtrip(self) -> None:
        segments = parse_subtitle(
            "WEBVTT\n\n00:00:01.000 --> 00:00:02.500\nHello\n",
            "vtt",
        )
        exported = export_subtitle(segments, "vtt")
        self.assertTrue(exported.startswith("WEBVTT"))
        self.assertIn("00:00:01.000 --> 00:00:02.500", exported)

    def test_validate_sorts_and_clamps(self) -> None:
        segments = parse_srt(
            "1\n00:00:04,000 --> 00:00:05,000\nsecond\n\n"
            "2\n00:00:01,000 --> 00:00:02,000\nfirst\n",
            duration=4.5,
        )
        self.assertEqual(segments[0].text, "first")
        self.assertEqual(segments[1].end, 4.5)


if __name__ == "__main__":
    unittest.main()
