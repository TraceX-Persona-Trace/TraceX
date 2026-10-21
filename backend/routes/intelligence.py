"""
Intelligence route — Chunk 7.

GET /api/investigations/{investigation_id}/intelligence

Returns structured, deterministic investigation intelligence derived from
real evidence, reconstruction attributes, and cross-investigation matching.
No AI, no external search, no synthetic data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.investigation import Investigation
from schemas.intelligence import IntelligenceResult
from services.intelligence import build_intelligence

router = APIRouter(
    prefix="/api/investigations",
    tags=["intelligence"],
)


@router.get(
    "/{investigation_id}/intelligence",
    response_model=IntelligenceResult,
)
def get_intelligence(
    investigation_id: int,
    db: Session = Depends(get_db),
):
    """
    Return structured intelligence for the given investigation.

    - Analyses all real evidence belonging to the investigation.
    - Runs cross-investigation matching (reuses Chunk 6 service).
    - Produces explainable signals with full evidence traceability.
    - Returns 404 when the investigation does not exist.
    - Never returns fabricated evidence or synthetic confidence.
    """
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id)
        .first()
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return build_intelligence(investigation_id, db)
