"""OSINT HTTP schemas for Chunk 8 Phase B.

Wraps Phase A ProviderResult values. Does not invent findings or statuses.
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from schemas.evidence import EvidenceResponse


class OsintLookupRequest(BaseModel):
    target: str = Field(..., min_length=1)
    target_type: Literal["domain", "username"]


class OsintFindingResponse(BaseModel):
    finding_type: str
    value: str
    details: Optional[Dict[str, Any]] = None


class OsintProviderResultResponse(BaseModel):
    provider: str
    status: str
    target: str
    target_type: str
    findings: List[OsintFindingResponse] = Field(default_factory=list)
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class OsintLookupResponse(BaseModel):
    investigation_id: int
    target: str
    target_type: str
    providers: List[OsintProviderResultResponse]
    evidence_created: List[EvidenceResponse]
    evidence_created_count: int
    generated_at: datetime
