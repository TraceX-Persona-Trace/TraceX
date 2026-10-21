"""
Reconstruction schemas for Chunk 5A.

These schemas represent a structured derivation of evidence belonging to a single
investigation. No AI inference, no synthetic confidence, no external data is
involved. All field values are sourced directly from existing Evidence rows.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ReconstructionAttribute(BaseModel):
    """
    A single structured attribute derived from one Evidence row.

    All fields map directly to columns on the Evidence model — nothing is
    invented or inferred.

    Chunk 6 change:
        label  = Evidence.title         (human-readable display label, unchanged)
        value  = Evidence.normalised_value  (canonical matchable value, new)
    Prior to Chunk 6, value mapped to Evidence.title. The separation is now clean:
    label is for display, value is for matching.
    """
    evidence_id: int
    evidence_type: str          # Evidence.evidence_type
    source_type: str            # Evidence.source_type
    source_name: str            # Evidence.source_name
    source_url: Optional[str]   # Evidence.source_url
    label: Optional[str]        # Evidence.title (human-readable display label)
    value: Optional[str]        # Evidence.normalised_value (canonical matchable value)
    detail: Optional[str]       # Evidence.content (supporting detail)
    confidence: float           # Evidence.confidence — set by original evidence entry
    collected_at: datetime      # Evidence.collected_at


class ReconstructionResult(BaseModel):
    """
    The full reconstruction result for one investigation.

    Status values:
        "ok"       — at least one evidence item was found and processed
        "empty"    — the investigation exists but has no evidence items
    """
    investigation_id: int
    status: str                             # "ok" | "empty"
    evidence_used: int                      # total Evidence rows processed
    attributes: List[ReconstructionAttribute]
    generated_at: datetime                  # server-side UTC timestamp of this derivation
