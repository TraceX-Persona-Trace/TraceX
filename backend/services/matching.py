"""
Matching service for Chunk 6.

Performs deterministic, explainable cross-investigation evidence matching.
No AI, no external search, no synthetic confidence values.

Matching rules (applied only where Evidence.normalised_value IS NOT NULL):

    evidence_type      rule                     normalisation applied
    ─────────────────────────────────────────────────────────────────
    email              exact, case-insensitive  .strip().lower()
    phone              digits only              strip all non-digit chars, compare
    username           exact, case-insensitive  .strip().lower()
    domain             exact, lowercase         .strip().lower()
    ip_address         exact string             .strip()

    social_profile, address, image, document, other — not matched
    (too ambiguous or free-text for reliable deterministic matching)

Traceability chain:
    MatchHit.query_evidence_id        → Evidence (source investigation)
    MatchHit.matched_evidence_id      → Evidence (matched investigation)
    MatchHit.matched_investigation_id → Investigation
    MatchHit.match_rule               → why it matched
    MatchHit.query_value              → exactly what was searched
    MatchHit.matched_value            → exactly what was found
"""
import re
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from models.evidence import Evidence
from models.investigation import Investigation
from schemas.matching import MatchHit, MatchResult


# ---- normalisation helpers ----

def _normalise_email(v: str) -> str:
    return v.strip().lower()


def _normalise_phone(v: str) -> str:
    """Strip everything except digits."""
    return re.sub(r"\D", "", v)


def _normalise_username(v: str) -> str:
    return v.strip().lower()


def _normalise_domain(v: str) -> str:
    return v.strip().lower()


def _normalise_ip(v: str) -> str:
    return v.strip()


# Maps evidence_type → (normaliser, match_rule_label)
_MATCHERS: dict = {
    "email":      (_normalise_email,    "exact_case_insensitive"),
    "phone":      (_normalise_phone,    "digits_normalised"),
    "username":   (_normalise_username, "exact_case_insensitive"),
    "domain":     (_normalise_domain,   "exact_case_insensitive"),
    "ip_address": (_normalise_ip,       "exact_string"),
}


def _prepare_query_attributes(
    source_inv_id: int,
    db: Session,
) -> List[Tuple[Evidence, str, str]]:
    """
    Return a list of (evidence_row, normalised_value, match_rule) tuples
    for all evidence in the source investigation that:
      - has a non-null normalised_value
      - has a matchable evidence_type
    """
    rows = (
        db.query(Evidence)
        .filter(
            Evidence.investigation_id == source_inv_id,
            Evidence.normalised_value.isnot(None),
        )
        .all()
    )
    result = []
    for ev in rows:
        if ev.evidence_type not in _MATCHERS:
            continue
        normaliser, rule = _MATCHERS[ev.evidence_type]
        normalised = normaliser(ev.normalised_value)
        if normalised:  # skip empty strings after normalisation
            result.append((ev, normalised, rule))
    return result


def build_matches(source_inv_id: int, db: Session) -> MatchResult:
    """
    Find all cross-investigation evidence that shares a normalised_value
    with the evidence of the source investigation.

    The source investigation itself is excluded from results.

    Args:
        source_inv_id: The ID of the already-verified Investigation.
        db:            Active SQLAlchemy session.

    Returns:
        MatchResult with hits or an appropriate status string.
    """
    query_attrs = _prepare_query_attributes(source_inv_id, db)

    if not query_attrs:
        return MatchResult(
            investigation_id=source_inv_id,
            query_attributes=0,
            hits=[],
            status="no_matchable_attributes",
            generated_at=datetime.utcnow(),
        )

    # Pre-fetch all investigations for title lookup (avoids N+1 queries)
    inv_titles: dict = {
        inv.id: inv.title
        for inv in db.query(Investigation).all()
    }

    hits: List[MatchHit] = []

    for source_ev, query_norm, match_rule in query_attrs:
        # Fetch all candidate evidence of the same type, outside source investigation,
        # that has a non-null normalised_value
        candidates = (
            db.query(Evidence)
            .filter(
                Evidence.evidence_type == source_ev.evidence_type,
                Evidence.investigation_id != source_inv_id,
                Evidence.normalised_value.isnot(None),
            )
            .all()
        )

        normaliser, _ = _MATCHERS[source_ev.evidence_type]

        for cand in candidates:
            cand_norm = normaliser(cand.normalised_value)
            if cand_norm and cand_norm == query_norm:
                hits.append(MatchHit(
                    query_evidence_id=source_ev.id,
                    matched_evidence_id=cand.id,
                    matched_investigation_id=cand.investigation_id,
                    matched_investigation_title=inv_titles.get(
                        cand.investigation_id, f"Investigation #{cand.investigation_id}"
                    ),
                    evidence_type=source_ev.evidence_type,
                    match_rule=match_rule,
                    query_value=query_norm,
                    matched_value=cand_norm,
                    source_confidence=cand.confidence,
                ))

    status = "ok" if hits else "no_matches"

    return MatchResult(
        investigation_id=source_inv_id,
        query_attributes=len(query_attrs),
        hits=hits,
        status=status,
        generated_at=datetime.utcnow(),
    )
