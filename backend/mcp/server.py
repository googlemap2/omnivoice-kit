from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, BinaryIO

import soundfile as sf
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from backend.services.transcription_service import DEFAULT_ASR_MODEL_ID, transcribe_file
from backend.services.speech_service import OMNIVOICE_LANGUAGE_CHOICES, generate_clone_with_speaker_id, get_profile_store
from backend.infrastructure.stores.histories import list_history
from backend.infrastructure.model_store import DEFAULT_MODEL_ID
from backend.paths import OUTPUTS_DIR


PROTOCOL_VERSION = "2024-11-05"
http_app = FastAPI(title="OmniVoice Kit MCP Server", version="0.1.0")


def text_content(value: Any) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(value, ensure_ascii=False, indent=2),
            }
        ]
    }


def voice_dict(profile: Any) -> dict[str, Any]:
    return {
        "id": profile.id,
        "name": profile.name,
        "type": profile.type,
        "language": profile.language,
        "prompt_path": profile.prompt_path,
        "tags": profile.tags or [],
        "favorite": profile.favorite,
        "notes": profile.notes,
        "preview_path": profile.preview_path,
    }


def list_voices_tool(_: dict[str, Any]) -> dict[str, Any]:
    return {
        "voices": [voice_dict(profile) for profile in get_profile_store().list_profiles()],
    }


def list_languages_tool(_: dict[str, Any]) -> dict[str, Any]:
    return {
        "languages": [{"id": item[1], "label": item[0]} for item in OMNIVOICE_LANGUAGE_CHOICES],
    }


def generate_speech_tool(arguments: dict[str, Any]) -> dict[str, Any]:
    text = str(arguments.get("text") or "").strip()
    voice = str(arguments.get("voice") or "").strip()
    if not text:
        raise ValueError("text is required.")
    if not voice:
        raise ValueError("voice is required.")

    output_path = Path(str(arguments.get("output_path") or OUTPUTS_DIR / "mcp" / "speech.wav"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio, status = generate_clone_with_speaker_id(
        text=text,
        speaker_id=voice,
        model_id=str(arguments.get("model") or DEFAULT_MODEL_ID),
        language=arguments.get("language"),
        instruct_items=arguments.get("instruct_items") or [],
        num_step=int(arguments.get("num_step") or 16),
        guidance_scale=float(arguments.get("guidance_scale") or 2.0),
        speed=float(arguments.get("speed") or 1.0),
        duration=arguments.get("duration"),
        denoise=bool(arguments.get("denoise", True)),
        preprocess_prompt=bool(arguments.get("preprocess_prompt", True)),
        postprocess_output=bool(arguments.get("postprocess_output", True)),
        effect_preset=str(arguments.get("effect_preset") or "raw"),
        record_history=False,
    )
    if audio is None:
        raise RuntimeError(status)
    sample_rate, samples = audio
    sf.write(output_path, samples, sample_rate, format="WAV", subtype="PCM_16")
    return {
        "output_path": str(output_path),
        "sample_rate": sample_rate,
        "status": status,
    }


def transcribe_audio_tool(arguments: dict[str, Any]) -> dict[str, Any]:
    input_path = str(arguments.get("input_path") or "").strip()
    if not input_path:
        raise ValueError("input_path is required.")
    result = transcribe_file(
        audio_path=input_path,
        model_id=str(arguments.get("model") or DEFAULT_ASR_MODEL_ID),
        language=arguments.get("language"),
        device=arguments.get("device"),
        compute_type=arguments.get("compute_type"),
        word_timestamps=bool(arguments.get("word_timestamps", False)),
        beam_size=int(arguments.get("beam_size") or 5),
    )
    return result.to_dict()


TOOLS = {
    "list_voices": {
        "description": "List local OmniVoice voice profiles.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": list_voices_tool,
    },
    "list_languages": {
        "description": "List supported OmniVoice language IDs.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": list_languages_tool,
    },
    "generate_speech": {
        "description": "Generate speech from text with a saved voice profile and write a WAV file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "voice": {"type": "string"},
                "output_path": {"type": "string"},
                "model": {"type": "string"},
                "language": {"type": ["string", "null"]},
                "effect_preset": {"type": "string", "enum": ["raw", "normalize", "broadcast"]},
                "num_step": {"type": "integer", "minimum": 1},
                "guidance_scale": {"type": "number"},
                "speed": {"type": "number"},
                "duration": {"type": ["number", "null"]},
                "instruct_items": {"type": "array", "items": {"type": "string"}},
                "denoise": {"type": "boolean"},
                "preprocess_prompt": {"type": "boolean"},
                "postprocess_output": {"type": "boolean"},
            },
            "required": ["text", "voice"],
            "additionalProperties": False,
        },
        "handler": generate_speech_tool,
    },
    "transcribe_audio": {
        "description": "Transcribe a local audio or video file with faster-whisper.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string"},
                "model": {"type": "string"},
                "language": {"type": ["string", "null"]},
                "device": {"type": ["string", "null"]},
                "compute_type": {"type": ["string", "null"]},
                "word_timestamps": {"type": "boolean"},
                "beam_size": {"type": "integer", "minimum": 1},
            },
            "required": ["input_path"],
            "additionalProperties": False,
        },
        "handler": transcribe_audio_tool,
    },
}


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]


def list_resources() -> list[dict[str, Any]]:
    return [
        {
            "uri": "backend://generation-history/recent",
            "name": "Recent generation history",
            "description": "Recent OmniVoice generation history from the configured PostgreSQL database.",
            "mimeType": "application/json",
        }
    ]


def read_resource(uri: str) -> dict[str, Any]:
    if uri != "backend://generation-history/recent":
        raise ValueError(f"Unknown resource URI: {uri}")
    try:
        data = list_history(limit=20)
    except Exception as e:
        data = {"error": f"{type(e).__name__}: {e}"}
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(data, ensure_ascii=False, indent=2),
            }
        ]
    }


def success(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    if request_id is None and isinstance(method, str) and method.startswith("notifications/"):
        return None

    try:
        if method == "initialize":
            return success(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "omnivoice-kit", "version": "0.1.0"},
                },
            )
        if method == "ping":
            return success(request_id, {})
        if method == "tools/list":
            return success(request_id, {"tools": list_tools()})
        if method == "tools/call":
            name = str(params.get("name") or "")
            arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
            spec = TOOLS.get(name)
            if spec is None:
                raise ValueError(f"Unknown tool: {name}")
            return success(request_id, text_content(spec["handler"](arguments)))
        if method == "resources/list":
            return success(request_id, {"resources": list_resources()})
        if method == "resources/read":
            return success(request_id, read_resource(str(params.get("uri") or "")))
        return error_response(request_id, -32601, f"Method not found: {method}")
    except Exception as e:
        return error_response(request_id, -32000, f"{type(e).__name__}: {e}")


@http_app.get("/health")
def http_health() -> dict[str, Any]:
    return {
        "object": "mcp_server",
        "transport": "http",
        "protocolVersion": PROTOCOL_VERSION,
        "tools": list(TOOLS),
    }


@http_app.post("/mcp")
async def http_mcp(request: Request) -> Response:
    payload = await request.json()
    if isinstance(payload, list):
        responses = [response for item in payload if (response := handle_http_item(item)) is not None]
        if not responses:
            return Response(status_code=202)
        return JSONResponse(responses)
    response = handle_http_item(payload)
    if response is None:
        return Response(status_code=202)
    return JSONResponse(response)


def handle_http_item(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return error_response(None, -32600, "Invalid JSON-RPC request.")
    return handle_request(payload)


def read_message(stream: BinaryIO) -> dict[str, Any] | None:
    first = stream.readline()
    if not first:
        return None
    if first.startswith(b"Content-Length:"):
        length = int(first.split(b":", 1)[1].strip())
        while True:
            line = stream.readline()
            if line in {b"\r\n", b"\n", b""}:
                break
        payload = stream.read(length)
    else:
        payload = first
    return json.loads(payload.decode("utf-8"))


def write_message(stream: BinaryIO, message: dict[str, Any]) -> None:
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stream.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload)
    stream.flush()


def serve_stdio() -> None:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        message = read_message(stdin)
        if message is None:
            return
        response = handle_request(message)
        if response is not None:
            write_message(stdout, response)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the OmniVoice Kit MCP server.")
    parser.add_argument("--stdio", action="store_true", help="Run the stdio MCP transport. This is the default.")
    parser.add_argument("--http", action="store_true", help="Run the HTTP JSON-RPC MCP transport.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host.")
    parser.add_argument("--port", type=int, default=8765, help="HTTP bind port.")
    args = parser.parse_args(argv)
    if args.http:
        import uvicorn

        uvicorn.run("backend.mcp.server:http_app", host=args.host, port=args.port)
        return
    serve_stdio()


if __name__ == "__main__":
    main()
