from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.investigation import Investigation
from schemas.investigation import (
    CreateInvestigationRequest,
    UpdateInvestigationRequest,
    InvestigationResponse,
    InvestigationListResponse,
)

router = APIRouter(prefix="/api/investigations", tags=["investigations"])

VALID_STATUSES = {"active", "archived"}
VALID_MODES = {"demo", "live"}


@router.post("", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
def create_investigation(payload: CreateInvestigationRequest, db: Session = Depends(get_db)):
    if payload.mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Allowed: {sorted(VALID_MODES)}")
    investigation = Investigation(
        title=payload.title,
        description=payload.description,
        mode=payload.mode,
        status="active",
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    return investigation


@router.get("", response_model=InvestigationListResponse)
def list_investigations(db: Session = Depends(get_db)):
    items = db.query(Investigation).order_by(Investigation.created_at.desc()).all()
    return InvestigationListResponse(items=items, total=len(items))


@router.get("/{investigation_id}", response_model=InvestigationResponse)
def get_investigation(investigation_id: int, db: Session = Depends(get_db)):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.patch("/{investigation_id}", response_model=InvestigationResponse)
def update_investigation(
    investigation_id: int,
    payload: UpdateInvestigationRequest,
    db: Session = Depends(get_db),
):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if payload.title is not None:
        investigation.title = payload.title
    if payload.description is not None:
        investigation.description = payload.description
    if payload.status is not None:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {sorted(VALID_STATUSES)}")
        investigation.status = payload.status
    if payload.mode is not None:
        if payload.mode not in VALID_MODES:
            raise HTTPException(status_code=400, detail=f"Invalid mode. Allowed: {sorted(VALID_MODES)}")
        investigation.mode = payload.mode

    investigation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(investigation)
    return investigation


@router.delete("/{investigation_id}", status_code=status.HTTP_200_OK)
def delete_investigation(investigation_id: int, db: Session = Depends(get_db)):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    db.delete(investigation)
    db.commit()
    return {"detail": "Investigation deleted"}
