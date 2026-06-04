from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.errors import websocket_error as _websocket_error
from backend.services.dictation_service import fake_result_event, partial_event, result_event, transcribe_audio_bytes
from backend.services.transcription_service import DEFAULT_ASR_MODEL_ID

router = APIRouter()

@router.get("/v1/dictation/status")
def get_dictation_status() -> dict:
    return {
        "object": "dictation_status",
        "data": {
            "websocket_path": "/v1/dictation/ws",
            "event_types": ["ready", "partial", "final", "done", "error"],
            "default_model": DEFAULT_ASR_MODEL_ID,
        },
    }


@router.websocket("/v1/dictation/ws")
async def websocket_dictation(
    websocket: WebSocket,
    model: str = DEFAULT_ASR_MODEL_ID,
    language: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
    word_timestamps: bool = False,
    beam_size: int = 5,
    test_mode: bool = False,
) -> None:
    await websocket.accept()
    audio_chunks: list[bytes] = []
    mime_type: str | None = None
    await websocket.send_json({"type": "ready"})
    try:
        while True:
            message = await websocket.receive()
            if message.get("bytes") is not None:
                chunk = message["bytes"]
                if chunk:
                    audio_chunks.append(chunk)
                    await websocket.send_json(partial_event(sum(len(item) for item in audio_chunks)))
                continue

            text = message.get("text")
            if text is None:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = {"type": text}

            event_type = payload.get("type")
            if event_type == "start":
                mime_type = payload.get("mime_type") or mime_type
                audio_chunks.clear()
                await websocket.send_json({"type": "ready"})
            elif event_type == "stop":
                audio_bytes = b"".join(audio_chunks)
                if test_mode:
                    await websocket.send_json(fake_result_event(audio_bytes))
                else:
                    result = transcribe_audio_bytes(
                        audio_bytes,
                        mime_type=mime_type,
                        model_id=model,
                        language=language,
                        device=device,
                        compute_type=compute_type,
                        word_timestamps=word_timestamps,
                        beam_size=beam_size,
                    )
                    await websocket.send_json(result_event(result))
                await websocket.send_json({"type": "done"})
                await websocket.close()
                return
            elif event_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        return
    except Exception as e:
        await _websocket_error(websocket, e)
        await websocket.close(code=1011)

