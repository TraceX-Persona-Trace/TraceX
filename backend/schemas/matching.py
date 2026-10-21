"""
Matching schemas for Chunk 6.

All fields are derived from real Evidence and Investigation rows.
No AI inference, no synthetic confidence, no external data.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel


class MatchHit(BaseModel):
    """
    A single cross-investigation evidence match.

    Traceability:
        query_evidence_id         → Evidence row in the source investigation
        matched_evidence_id       → Evidence row in another investigation
        matched_investigation_id  → Investigation that owns the matched evidence
    """
    query_evidence_id: int
    matched_evidence_id: int
    matched_investigation_id: int
    matched_investigation_title: str  # avoids a second frontend request
    evidence_type: str
    match_rule: str       # e.g. "exact_case_insensitive", "digits_normalised"
    query_value: str      # the normalised value that was searched
    matched_value: str    # the normalised value that was found
    source_confidence: float  # Evidence.confidence of the matched row (real, not synthetic)


class MatchResult(BaseModel):
    """
    Full matching result for one investigation.

    Status values:
        "ok"                       — at least one cross-investigation match found
        "no_matches"               — matchable attributes found, but no cross-investigation overlap
        "no_matchable_attributes"  — no evidence has a non-null normalised_value
    """
    investigation_id: int
    query_attributes: int   # number of evidence items that were eligible to match
    hits: List[MatchHit]
    status: str
    generated_at: datetime
