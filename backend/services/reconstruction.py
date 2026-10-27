"""
Reconstruction service for Chunk 5A.

Derives a structured ReconstructionResult from the real Evidence rows stored
for an investigation. No AI inference, no external search, no synthetic data.

Traceability chain:
    ReconstructionResult
        → ReconstructionAttribute (one per Evidence row)
            → Evidence.id (evidence_id)
                → Investigation.id (investigation_id)
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.models.evidence import Evidence
from backend.schemas.reconstruction import ReconstructionAttribute, ReconstructionResult


def build_reconstruction(investigation_id: int, db: Session) -> ReconstructionResult:
    """
    Read all Evidence rows for the given investigation and convert each one
    into a ReconstructionAttribute.

    Ordering: by evidence_type (alphabetical) then by confidence descending,
    so that the result is deterministic and the highest-confidence items for
    each type appear first.

    Args:
        investigation_id: The ID of the already-verified Investigation.
        db: Active SQLAlchemy session.

    Returns:
        ReconstructionResult with status "ok" (evidence found) or "empty"
        (no evidence rows exist for this investigation).
    """
    evidence_rows = (
        db.query(Evidence)
        .filter(Evidence.investigation_id == investigation_id)
        .order_by(Evidence.evidence_type, Evidence.confidence.desc())
        .all()
    )

    attributes = [
        ReconstructionAttribute(
            evidence_id=ev.id,
            evidence_type=ev.evidence_type,
            source_type=ev.source_type,
            source_name=ev.source_name,
            source_url=ev.source_url,
            label=ev.title,                   # human-readable display label (Evidence.title)
            value=ev.normalised_value,         # canonical matchable value (Evidence.normalised_value)
            detail=ev.content,                 # supporting detail — may be None
            confidence=ev.confidence,
            collected_at=ev.collected_at,
        )
        for ev in evidence_rows
    ]

    return ReconstructionResult(
        investigation_id=investigation_id,
        status="ok" if attributes else "empty",
        evidence_used=len(attributes),
        attributes=attributes,
        generated_at=datetime.now(timezone.utc),
    )
