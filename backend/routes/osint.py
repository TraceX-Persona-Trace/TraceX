'''OSINT route – integrates run_osint_lookup service.
Provides POST /api/investigations/{investigation_id}/osint
Validates investigation existence, uses request/response schemas, and returns created evidence.
'''

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.investigation import Investigation
from backend.schemas.osint import OsintLookupRequest, OsintLookupResponse
from backend.services.osint import run_osint_lookup

router = APIRouter(
    prefix="/api/investigations/{investigation_id}",
    tags=["osint"],
)

def _get_investigation_or_404(investigation_id: int, db: Session) -> Investigation:
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv

@router.post(
    "/osint",
    response_model=OsintLookupResponse,
    status_code=status.HTTP_200_OK,
)
def osint_lookup(
    investigation_id: int,
    payload: OsintLookupRequest,
    db: Session = Depends(get_db),
):
    inv = _get_investigation_or_404(investigation_id, db)

    norm_target, resolved_type, provider_results, created_evidence = run_osint_lookup(
        investigation=inv,
        target=payload.target,
        target_type=payload.target_type,
        db=db,
    )

    # Convert ProviderResult objects to plain dicts for Pydantic validation
    providers = []
    for pr in provider_results:
        if hasattr(pr, "to_dict"):
            providers.append(pr.to_dict())
        else:
            providers.append(pr)

    return OsintLookupResponse(
        investigation_id=investigation_id,
        target=norm_target,
        target_type=resolved_type,
        providers=providers,
        evidence_created=created_evidence,
        evidence_created_count=len(created_evidence),
        generated_at=datetime.now(timezone.utc),
    )
