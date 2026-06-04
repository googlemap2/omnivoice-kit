from pydantic import BaseModel

from backend.infrastructure.model_store import DEFAULT_MODEL_ID


class ModelInstallRequest(BaseModel):
    repo_id: str = DEFAULT_MODEL_ID
    hf_token: str | None = None

