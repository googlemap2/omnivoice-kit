import logging
import traceback

from fastapi import HTTPException, WebSocket


logger = logging.getLogger("voicekit.api")


def generation_error(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


def server_error(e: Exception) -> HTTPException:
    logger.error("%s: %s\n%s", type(e).__name__, e, traceback.format_exc())
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


async def websocket_error(websocket: WebSocket, e: Exception) -> None:
    logger.error("%s: %s\n%s", type(e).__name__, e, traceback.format_exc())
    await websocket.send_json({"type": "error", "message": f"{type(e).__name__}: {e}"})

