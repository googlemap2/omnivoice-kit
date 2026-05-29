import unittest
from importlib.util import find_spec

from voicekit.dictation import fake_result_event, media_suffix_from_mime, partial_event


class DictationProtocolTests(unittest.TestCase):
    def test_media_suffix_from_mime(self) -> None:
        self.assertEqual(media_suffix_from_mime("audio/webm;codecs=opus"), ".webm")
        self.assertEqual(media_suffix_from_mime("audio/ogg"), ".ogg")
        self.assertEqual(media_suffix_from_mime("audio/mpeg"), ".mp3")
        self.assertEqual(media_suffix_from_mime(None), ".wav")

    def test_partial_event_reports_bytes_received(self) -> None:
        self.assertEqual(partial_event(42), {"type": "partial", "text": "", "bytes_received": 42})

    def test_fake_result_event_matches_websocket_schema(self) -> None:
        event = fake_result_event(b"abc")
        self.assertEqual(event["type"], "final")
        self.assertEqual(event["bytes_received"], 3)
        self.assertEqual(event["segments"], [])
        self.assertIn("fake dictation transcript", event["text"])

    @unittest.skipIf(
        any(find_spec(name) is None for name in ("fastapi", "soundfile", "numpy", "omnivoice")),
        "API dependencies are not installed.",
    )
    def test_websocket_protocol_with_fake_asr(self) -> None:
        from fastapi.testclient import TestClient
        from voicekit.api import app

        client = TestClient(app)
        with client.websocket_connect("/v1/dictation/ws?test_mode=true") as websocket:
            self.assertEqual(websocket.receive_json()["type"], "ready")
            websocket.send_json({"type": "start", "mime_type": "audio/webm"})
            self.assertEqual(websocket.receive_json()["type"], "ready")
            websocket.send_bytes(b"abc")
            partial = websocket.receive_json()
            self.assertEqual(partial["type"], "partial")
            self.assertEqual(partial["bytes_received"], 3)
            websocket.send_json({"type": "stop"})
            final = websocket.receive_json()
            self.assertEqual(final["type"], "final")
            self.assertEqual(final["bytes_received"], 3)
            self.assertEqual(websocket.receive_json()["type"], "done")


if __name__ == "__main__":
    unittest.main()
