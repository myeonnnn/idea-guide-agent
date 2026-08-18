from datetime import datetime
from pydantic import BaseModel, Field


class SessionState(BaseModel):
    id: str
    idea: str
    stage_index: int = 0
    stage_outputs: dict[str, dict] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
