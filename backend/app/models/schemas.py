from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DetectionMethod(str, Enum):
    REGEX = "regex"
    NER = "ner"
    CONTEXT = "context"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Entity(BaseModel):
    entity_type: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    confidence: float = Field(ge=0, le=1)
    detection_method: DetectionMethod
    risk_level: RiskLevel


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000_000)
    masking_mode: str = Field(default="typed", pattern="^(typed|black|partial)$")


class DetectResponse(BaseModel):
    entities: list[Entity]
    entity_count: int


class RedactResponse(BaseModel):
    redacted_text: str
    entities: list[Entity]
    entity_count: int


class DocumentResponse(BaseModel):
    filename: str
    media_type: str
    extracted_text: str | None = None
    redacted_text: str | None = None
    entities: list[Entity]
    entity_count: int
    extracted_characters: int
    metadata: dict[str, Any] = {}
