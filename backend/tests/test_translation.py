import unittest

from backend.services.translation_service import (
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
        from backend.domain.settings import AppSettings

        provider = PassthroughProvider()
        available, message = provider.availability(AppSettings())
        self.assertTrue(available)
        self.assertIsNone(message)

    def test_format_transcription_with_translation_keeps_source_text(self) -> None:
        from backend.services.transcription_service import TranscriptionResult, TranscriptionSegment, format_transcription_with_translation

        result = TranscriptionResult(
            text="Hello world",
            language="en",
            duration=1.0,
            segments=[TranscriptionSegment(id=0, start=0.0, end=1.0, text="Hello world")],
        )

        payload = format_transcription_with_translation(
            result,
            "verbose_json",
            source_language="en",
            target_language="vi",
            provider_id="passthrough",
        )

        self.assertIsInstance(payload, dict)
        assert isinstance(payload, dict)
        self.assertEqual(payload["translation"]["target_language"], "vi")
        self.assertEqual(payload["segments"][0]["metadata"]["source_text"], "Hello world")


if __name__ == "__main__":
    unittest.main()
