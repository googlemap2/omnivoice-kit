import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient

from voicekit import mcp_server


class McpServerTests(unittest.TestCase):
    def test_tools_list_contains_core_tools(self):
        response = mcp_server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(response["result"]["tools"][0]["name"], "list_voices")
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("generate_speech", names)
        self.assertIn("transcribe_audio", names)

    def test_list_voices_tool(self):
        profile = SimpleNamespace(
            id="adam1",
            name="Adam",
            type="clone",
            language="en",
            prompt_path="assets/voices/adam1/prompt.pt",
            tags=["male"],
            favorite=True,
            notes="test",
            preview_path=None,
        )
        store = SimpleNamespace(list_profiles=lambda: [profile])
        with patch("voicekit.mcp_server.get_profile_store", return_value=store):
            response = mcp_server.handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "list_voices", "arguments": {}},
                }
            )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["voices"][0]["id"], "adam1")
        self.assertTrue(payload["voices"][0]["favorite"])

    def test_generate_speech_tool_writes_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "speech.wav"
            with patch(
                "voicekit.mcp_server.generate_clone_with_speaker_id",
                return_value=((24000, np.zeros(240, dtype=np.int16)), "Done."),
            ) as generate:
                response = mcp_server.handle_request(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "generate_speech",
                            "arguments": {
                                "text": "hello",
                                "voice": "adam1",
                                "output_path": str(output_path),
                            },
                        },
                    }
                )
            payload = json.loads(response["result"]["content"][0]["text"])
            self.assertEqual(payload["output_path"], str(output_path))
            self.assertTrue(output_path.is_file())
            self.assertFalse(generate.call_args.kwargs["record_history"])

    def test_recent_history_resource_handles_database_error(self):
        with patch("voicekit.mcp_server.list_history", side_effect=RuntimeError("missing db")):
            response = mcp_server.handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "resources/read",
                    "params": {"uri": "voicekit://generation-history/recent"},
                }
            )
        payload = json.loads(response["result"]["contents"][0]["text"])
        self.assertIn("missing db", payload["error"])

    def test_http_health(self):
        client = TestClient(mcp_server.http_app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transport"], "http")
        self.assertIn("list_voices", response.json()["tools"])

    def test_http_mcp_tools_list(self):
        client = TestClient(mcp_server.http_app)
        response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 5, "method": "tools/list"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 5)
        self.assertIn("tools", response.json()["result"])

    def test_http_mcp_batch_and_notification(self):
        client = TestClient(mcp_server.http_app)
        response = client.post(
            "/mcp",
            json=[
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 6, "method": "ping"},
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"jsonrpc": "2.0", "id": 6, "result": {}}])

    def test_http_mcp_only_notification(self):
        client = TestClient(mcp_server.http_app)
        response = client.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertEqual(response.status_code, 202)


if __name__ == "__main__":
    unittest.main()
