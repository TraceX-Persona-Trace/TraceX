"""
Matching route — Chunk 6.

POST /api/investigations/{investigation_id}/match

Performs deterministic cross-investigation evidence matching using
real stored normalised_value fields. No AI, no external search.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.investigation import Investigation
from schemas.matching import MatchResult
from services.matching import build_matches

router = APIRouter(
    prefix="/api/investigations",
    tags=["matching"],
)


@router.post(
    "/{investigation_id}/match",
    response_model=MatchResult,
)
def match_investigation(
    investigation_id: int,
    db: Session = Depends(get_db),
):
    """
    Find cross-investigation evidence that shares a normalised_value with
    the evidence stored for the given investigation.

    - Returns status "ok" when at least one match is found.
    - Returns status "no_matches" when matchable attributes exist but nothing matches.
    - Returns status "no_matchable_attributes" when no evidence has normalised_value set.
    - Returns 404 when the investigation does not exist.
    """
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id)
        .first()
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return build_matches(investigation_id, db)
