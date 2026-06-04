from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.app.dependencies import output_file_response


router = APIRouter()


@router.get("/v1/files")
def get_output_file(path: str) -> FileResponse:
    return output_file_response(path)

