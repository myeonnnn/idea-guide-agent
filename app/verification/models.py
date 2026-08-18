from enum import Enum

from pydantic import BaseModel


class SourceTier(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    ESTIMATE = "ESTIMATE"


class Claim(BaseModel):
    text: str
    source_tier: SourceTier
    source_url: str | None = None
