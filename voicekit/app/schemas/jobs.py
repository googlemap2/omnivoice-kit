from typing import Any

from pydantic import BaseModel, Field

from voicekit.stores.jobs import JobType


class JobCreateRequest(BaseModel):
    type: JobType
    params: dict[str, Any] = Field(default_factory=dict)

