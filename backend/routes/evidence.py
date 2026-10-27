from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.investigation import Investigation
from backend.models.evidence import Evidence
from backend.schemas.evidence import (
    CreateEvidenceRequest,
    UpdateEvidenceRequest,
    EvidenceResponse,
    EvidenceListResponse,
)

router = APIRouter(
    prefix="/api/investigations/{investigation_id}/evidence",
    tags=["evidence"],
)


def _get_investigation_or_404(investigation_id: int, db: Session) -> Investigation:
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


def _get_evidence_or_404(evidence_id: int, investigation_id: int, db: Session) -> Evidence:
    ev = (
        db.query(Evidence)
        .filter(Evidence.id == evidence_id, Evidence.investigation_id == investigation_id)
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev


@router.post("", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def create_evidence(
    investigation_id: int,
    payload: CreateEvidenceRequest,
    db: Session = Depends(get_db),
):
    _get_investigation_or_404(investigation_id, db)
    ev = Evidence(
        investigation_id=investigation_id,
        source_type=payload.source_type,
        source_name=payload.source_name,
        source_url=payload.source_url,
        title=payload.title,
        content=payload.content,
        evidence_type=payload.evidence_type,
        confidence=payload.confidence,
        metadata_json=payload.metadata_json,
        normalised_value=payload.normalised_value,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


@router.get("", response_model=EvidenceListResponse)
def list_evidence(investigation_id: int, db: Session = Depends(get_db)):
    _get_investigation_or_404(investigation_id, db)
    items = (
        db.query(Evidence)
        .filter(Evidence.investigation_id == investigation_id)
        .order_by(Evidence.collected_at.desc())
        .all()
    )
    return EvidenceListResponse(items=items, total=len(items))


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(investigation_id: int, evidence_id: int, db: Session = Depends(get_db)):
    _get_investigation_or_404(investigation_id, db)
    return _get_evidence_or_404(evidence_id, investigation_id, db)


@router.patch("/{evidence_id}", response_model=EvidenceResponse)
def update_evidence(
    investigation_id: int,
    evidence_id: int,
    payload: UpdateEvidenceRequest,
    db: Session = Depends(get_db),
):
    _get_investigation_or_404(investigation_id, db)
    ev = _get_evidence_or_404(evidence_id, investigation_id, db)

    if payload.source_type is not None:
        ev.source_type = payload.source_type
    if payload.source_name is not None:
        ev.source_name = payload.source_name
    if payload.source_url is not None:
        ev.source_url = payload.source_url
    if payload.title is not None:
        ev.title = payload.title
    if payload.content is not None:
        ev.content = payload.content
    if payload.evidence_type is not None:
        ev.evidence_type = payload.evidence_type
    if payload.confidence is not None:
        ev.confidence = payload.confidence
    if payload.metadata_json is not None:
        ev.metadata_json = payload.metadata_json
    if payload.normalised_value is not None:
        ev.normalised_value = payload.normalised_value

    db.commit()
    db.refresh(ev)
    return ev


@router.delete("/{evidence_id}", status_code=status.HTTP_200_OK)
def delete_evidence(investigation_id: int, evidence_id: int, db: Session = Depends(get_db)):
    _get_investigation_or_404(investigation_id, db)
    ev = _get_evidence_or_404(evidence_id, investigation_id, db)
    db.delete(ev)
    db.commit()
    return {"detail": "Evidence deleted"}
