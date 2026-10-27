"""
Seed route — creates a fixed demo investigation with pre-populated evidence items.
Idempotent: if the demo investigation already exists (matched by title), it returns
the existing record without duplicating data.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.investigation import Investigation
from backend.models.evidence import Evidence
from backend.schemas.investigation import InvestigationResponse

router = APIRouter(prefix="/api/seed", tags=["seed"])

DEMO_TITLE = "TraceX Demo Investigation"

DEMO_EVIDENCE = [
    {
        "source_type": "demo",
        "source_name": "LinkedIn",
        "source_url": "https://www.linkedin.com/in/demo-profile",
        "title": "LinkedIn Profile",
        "content": "Professional profile found for subject. Listed employer: Acme Corp. Location: San Francisco, CA.",
        "evidence_type": "social_profile",
        "confidence": 0.9,
    },
    {
        "source_type": "demo",
        "source_name": "Twitter / X",
        "source_url": "https://twitter.com/demo_handle",
        "title": "Twitter Account",
        "content": "Public account @demo_handle. 1,200 followers. Account created 2018. Bio mentions 'software engineer'.",
        "evidence_type": "social_profile",
        "confidence": 0.75,
    },
    {
        "source_type": "demo",
        "source_name": "Manual Entry",
        "source_url": None,
        "title": "Primary Email Address",
        "content": "demo.subject@example.com — confirmed via account registration leak data (demo only).",
        "evidence_type": "email",
        "confidence": 0.85,
    },
    {
        "source_type": "demo",
        "source_name": "WHOIS Lookup",
        "source_url": "https://who.is/whois/demo-domain.example",
        "title": "Registered Domain",
        "content": "demo-domain.example registered 2020-03-15. Registrant email matches primary email.",
        "evidence_type": "domain",
        "confidence": 0.7,
    },
    {
        "source_type": "demo",
        "source_name": "GitHub",
        "source_url": "https://github.com/demo-user",
        "title": "GitHub Username",
        "content": "Username demo-user. 34 public repositories. Primary language: Python. Last active recently.",
        "evidence_type": "username",
        "confidence": 0.8,
    },
]


@router.post("/demo", response_model=InvestigationResponse, status_code=200)
def seed_demo(db: Session = Depends(get_db)):
    """
    Create (or return existing) demo investigation pre-loaded with evidence items.
    Safe to call multiple times — idempotent on investigation title.
    """
    existing = (
        db.query(Investigation)
        .filter(Investigation.title == DEMO_TITLE)
        .first()
    )
    if existing:
        return existing

    inv = Investigation(
        title=DEMO_TITLE,
        description=(
            "A pre-seeded demonstration investigation showing how TraceX "
            "organises evidence items. No real subjects are involved."
        ),
        status="active",
        mode="demo",
    )
    db.add(inv)
    db.flush()  # get inv.id before adding children

    now = datetime.now(timezone.utc)
    for item in DEMO_EVIDENCE:
        ev = Evidence(
            investigation_id=inv.id,
            collected_at=now,
            **item,
        )
        db.add(ev)

    db.commit()
    db.refresh(inv)
    return inv
