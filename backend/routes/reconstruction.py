"""
Reconstruction route — Chunk 5A.

POST /api/investigations/{investigation_id}/reconstruct

Derives a structured profile from the real evidence belonging to the given
investigation. No AI, no external search, no synthetic data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.investigation import Investigation
from schemas.reconstruction import ReconstructionResult
from services.reconstruction import build_reconstruction

router = APIRouter(
    prefix="/api/investigations",
    tags=["reconstruction"],
)


@router.post(
    "/{investigation_id}/reconstruct",
    response_model=ReconstructionResult,
)
def reconstruct_investigation(
    investigation_id: int,
    db: Session = Depends(get_db),
):
    """
    Derive a structured reconstruction result from the evidence stored for the
    given investigation.

    - Returns status "ok" with all attributes when evidence exists.
    - Returns status "empty" with an empty attributes list when no evidence exists.
    - Returns 404 when the investigation does not exist.
    """
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id)
        .first()
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return build_reconstruction(investigation_id, db)
