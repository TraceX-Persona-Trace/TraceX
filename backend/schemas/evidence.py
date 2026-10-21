from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator


VALID_EVIDENCE_TYPES = {
    "social_profile",
    "email",
    "phone",
    "address",
    "username",
    "image",
    "document",
    "domain",
    "ip_address",
    "other",
}

VALID_SOURCE_TYPES = {
    "manual",
    "osint",
    "import",
    "demo",
}


class CreateEvidenceRequest(BaseModel):
    source_type: str = "manual"
    source_name: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    evidence_type: str
    confidence: float = 0.0
    metadata_json: Optional[str] = None
    normalised_value: Optional[str] = None  # Chunk 6: canonical matchable value

    @field_validator("evidence_type")
    @classmethod
    def validate_evidence_type(cls, v: str) -> str:
        if v not in VALID_EVIDENCE_TYPES:
            raise ValueError(f"Invalid evidence_type. Allowed: {sorted(VALID_EVIDENCE_TYPES)}")
        return v

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        if v not in VALID_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type. Allowed: {sorted(VALID_SOURCE_TYPES)}")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class UpdateEvidenceRequest(BaseModel):
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    evidence_type: Optional[str] = None
    confidence: Optional[float] = None
    metadata_json: Optional[str] = None
    normalised_value: Optional[str] = None  # Chunk 6: canonical matchable value

    @field_validator("evidence_type")
    @classmethod
    def validate_evidence_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_EVIDENCE_TYPES:
            raise ValueError(f"Invalid evidence_type. Allowed: {sorted(VALID_EVIDENCE_TYPES)}")
        return v

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type. Allowed: {sorted(VALID_SOURCE_TYPES)}")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class EvidenceResponse(BaseModel):
    id: int
    investigation_id: int
    source_type: str
    source_name: str
    source_url: Optional[str]
    title: Optional[str]
    content: Optional[str]
    evidence_type: str
    confidence: float
    collected_at: datetime
    metadata_json: Optional[str]
    normalised_value: Optional[str]  # Chunk 6: canonical matchable value

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    items: List[EvidenceResponse]
    total: int
