import unittest

from voicekit.translation import (
    PassthroughProvider,
    list_providers,
    normalize_segments,
    translate_segments,
    translate_text,
)


class TranslationPassthroughTests(unittest.TestCase):
    def test_passthrough_translate_text(self) -> None:
        result = translate_text(
            text="Xin chao",
            source_language="vi",
            target_language="en",
            provider_id="passthrough",
        )
        self.assertEqual(result.text, "Xin chao")
        self.assertEqual(result.provider, "passthrough")

    def test_passthrough_translate_segments(self) -> None:
        segments = [
            {"id": 0, "start": 0.0, "end": 1.2, "text": "Xin chao"},
            {"id": 1, "start": 1.2, "end": 2.4, "text": "the gioi"},
        ]
        result = translate_segments(
            segments=segments,
            source_language="vi",
            target_language="en",
            provider_id="passthrough",
        )
        self.assertEqual(len(result.segments or []), 2)
        assert result.segments is not None
        self.assertEqual(result.segments[0].translated_text, "Xin chao")
        self.assertEqual(result.segments[1].translated_text, "the gioi")
        self.assertEqual(result.text, "Xin chao the gioi")

    def test_normalize_segments_skips_empty_text(self) -> None:
        segments = normalize_segments(
            [
                {"id": 0, "text": "hello"},
                {"id": 1, "text": "   "},
            ]
        )
        self.assertEqual(len(segments), 1)

    def test_list_providers_includes_passthrough_available(self) -> None:
        providers = {item.id: item for item in list_providers()}
        self.assertIn("passthrough", providers)
        self.assertTrue(providers["passthrough"].available)

    def test_passthrough_provider_direct(self) -> None:
        from voicekit.settings import AppSettings

        provider = PassthroughProvider()
        available, message = provider.availability(AppSettings())
        self.assertTrue(available)
        self.assertIsNone(message)


if __name__ == "__main__":
    unittest.main()
