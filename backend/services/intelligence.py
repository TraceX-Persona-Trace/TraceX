"""
Intelligence service for Chunk 7.

Produces structured, deterministic investigation intelligence by consuming:
  - Evidence rows (via direct DB query)
  - Reconstruction results (via build_reconstruction)
  - Matching results (via build_matches)

No AI, no external search, no synthetic confidence values.

Provider abstraction:
    The service is split into two layers:
      1. _run_deterministic_analysis() — always runs, produces explainable signals
      2. build_intelligence() — orchestrates the above and sets provider="deterministic"

    When a future AI provider is configured, a new function (e.g.
    _run_ai_analysis()) can be called from build_intelligence() to append
    additional signals. It would set provider="openai" or similar. The
    deterministic signals remain unchanged — the AI layer is purely additive.

Traceability:
    Every IntelligenceSignal.evidence_ids refers to real Evidence.id values.
    Every IntelligenceSignal.investigation_ids refers to real Investigation.id values.
    No fabricated evidence is created.
"""
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from models.evidence import Evidence
from schemas.intelligence import (
    IntelligenceSignal,
    IntelligenceResult,
    SIGNAL_CROSS_INVESTIGATION_MATCH,
    SIGNAL_REPEATED_ATTRIBUTE,
    SIGNAL_HIGH_CONFIDENCE_EVIDENCE,
    SIGNAL_NO_MATCHABLE_ATTRIBUTES,
    SIGNAL_NO_CROSS_INVESTIGATION,
    SIGNAL_NO_EVIDENCE,
    SEVERITY_INFO,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
)
from services.matching import build_matches
from schemas.matching import MatchHit


# Threshold above which an evidence item is considered "high confidence"
HIGH_CONFIDENCE_THRESHOLD = 0.85


def _signal_no_evidence(inv_id: int) -> IntelligenceSignal:
    return IntelligenceSignal(
        signal_type=SIGNAL_NO_EVIDENCE,
        title="No evidence recorded",
        explanation=(
            "This investigation has no evidence items. "
            "Add evidence to enable reconstruction, matching, and intelligence."
        ),
        severity=SEVERITY_INFO,
        evidence_ids=[],
        investigation_ids=[inv_id],
    )


def _signal_no_matchable_attrs(inv_id: int, evidence_count: int) -> IntelligenceSignal:
    return IntelligenceSignal(
        signal_type=SIGNAL_NO_MATCHABLE_ATTRIBUTES,
        title="No matchable attributes",
        explanation=(
            f"This investigation has {evidence_count} evidence item(s) but none have a "
            "Matchable Value set. Set a normalised value on email, phone, username, "
            "domain, or IP address evidence to enable cross-investigation matching."
        ),
        severity=SEVERITY_INFO,
        evidence_ids=[],
        investigation_ids=[inv_id],
    )


def _signal_no_cross_investigation(inv_id: int, query_attributes: int) -> IntelligenceSignal:
    return IntelligenceSignal(
        signal_type=SIGNAL_NO_CROSS_INVESTIGATION,
        title="No cross-investigation matches found",
        explanation=(
            f"{query_attributes} matchable attribute(s) were checked against all other "
            "investigations. No shared values were found. This investigation's evidence "
            "does not overlap with any other currently known investigation."
        ),
        severity=SEVERITY_INFO,
        evidence_ids=[],
        investigation_ids=[inv_id],
    )


def _signals_from_hits(inv_id: int, hits: List[MatchHit]) -> List[IntelligenceSignal]:
    """
    Convert matching hits into intelligence signals.

    Two signal types:
        1. cross_investigation_match — one signal per unique (evidence_type, matched_inv) pair,
           grouping all hits with the same type and target investigation.
        2. repeated_attribute — raised when the same normalised value appears in 3 or more
           investigations (the source + 2 or more others), indicating a strongly shared identity
           attribute across the corpus.
    """
    signals: List[IntelligenceSignal] = []

    # ---- Signal type 1: cross_investigation_match ----
    # Group by (evidence_type, matched_investigation_id) to avoid one signal per hit.
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for hit in hits:
        key = (hit.evidence_type, hit.matched_investigation_id)
        groups[key].append(hit)

    for (ev_type, matched_inv_id), group_hits in groups.items():
        # Use the highest source_confidence among the group hits as the representative
        best_hit = max(group_hits, key=lambda h: h.source_confidence)
        # Determine severity from confidence
        if best_hit.source_confidence >= 0.85:
            sev = SEVERITY_HIGH
        elif best_hit.source_confidence >= 0.65:
            sev = SEVERITY_MEDIUM
        else:
            sev = SEVERITY_LOW

        ev_ids = [h.query_evidence_id for h in group_hits]
        # deduplicate while preserving order
        seen = set()
        ev_ids_dedup = [e for e in ev_ids if not (e in seen or seen.add(e))]

        signals.append(IntelligenceSignal(
            signal_type=SIGNAL_CROSS_INVESTIGATION_MATCH,
            title=f"Cross-investigation match: {ev_type}",
            explanation=(
                f"Evidence of type '{ev_type}' with value '{best_hit.query_value}' "
                f"matches evidence in investigation '{best_hit.matched_investigation_title}' "
                f"(id={matched_inv_id}) using rule '{best_hit.match_rule}'."
            ),
            severity=sev,
            evidence_ids=ev_ids_dedup,
            investigation_ids=[inv_id, matched_inv_id],
            match_rule=best_hit.match_rule,
            attribute_value=best_hit.query_value,
            evidence_type=ev_type,
            source_confidence=best_hit.source_confidence,
        ))

    # ---- Signal type 2: repeated_attribute ----
    # Count how many distinct investigations each normalised value appears in (including source).
    from collections import Counter
    value_inv_map: dict = defaultdict(set)
    for hit in hits:
        value_inv_map[(hit.evidence_type, hit.query_value)].add(hit.matched_investigation_id)
        value_inv_map[(hit.evidence_type, hit.query_value)].add(inv_id)

    for (ev_type, norm_val), inv_set in value_inv_map.items():
        if len(inv_set) >= 3:
            # Gather all source evidence IDs for this value
            rel_hits = [h for h in hits if h.evidence_type == ev_type and h.query_value == norm_val]
            ev_ids = list({h.query_evidence_id for h in rel_hits})
            signals.append(IntelligenceSignal(
                signal_type=SIGNAL_REPEATED_ATTRIBUTE,
                title=f"Attribute shared across {len(inv_set)} investigations: {ev_type}",
                explanation=(
                    f"The {ev_type} value '{norm_val}' appears in {len(inv_set)} investigations "
                    f"(ids: {sorted(inv_set)}). This attribute may represent a persistent identity "
                    "signal across multiple cases."
                ),
                severity=SEVERITY_HIGH,
                evidence_ids=ev_ids,
                investigation_ids=sorted(inv_set),
                attribute_value=norm_val,
                evidence_type=ev_type,
            ))

    return signals


def _signals_high_confidence(inv_id: int, evidence_rows: list) -> List[IntelligenceSignal]:
    """
    Raise a signal for each evidence item with confidence >= HIGH_CONFIDENCE_THRESHOLD.
    These are the strongest individual evidence points in the investigation.
    """
    signals = []
    for ev in evidence_rows:
        if ev.confidence >= HIGH_CONFIDENCE_THRESHOLD:
            label = ev.title or ev.source_name
            signals.append(IntelligenceSignal(
                signal_type=SIGNAL_HIGH_CONFIDENCE_EVIDENCE,
                title=f"High-confidence evidence: {label}",
                explanation=(
                    f"Evidence item '{label}' (type: {ev.evidence_type}, "
                    f"source: {ev.source_name}) has confidence {ev.confidence:.0%}, "
                    "which exceeds the high-confidence threshold."
                ),
                severity=SEVERITY_MEDIUM,
                evidence_ids=[ev.id],
                investigation_ids=[inv_id],
                evidence_type=ev.evidence_type,
                source_confidence=ev.confidence,
            ))
    return signals


def _run_deterministic_analysis(inv_id: int, db: Session) -> tuple:
    """
    Perform the full deterministic analysis.

    Returns: (signals, evidence_count)
    """
    # Load all evidence
    evidence_rows = (
        db.query(Evidence)
        .filter(Evidence.investigation_id == inv_id)
        .order_by(Evidence.evidence_type, Evidence.confidence.desc())
        .all()
    )

    signals: List[IntelligenceSignal] = []

    # ---- No evidence at all ----
    if not evidence_rows:
        return [_signal_no_evidence(inv_id)], 0

    # ---- High-confidence evidence signals ----
    signals.extend(_signals_high_confidence(inv_id, evidence_rows))

    # ---- Run matching (reuses Chunk 6 service, no duplication) ----
    match_result = build_matches(inv_id, db)

    if match_result.status == "no_matchable_attributes":
        signals.append(_signal_no_matchable_attrs(inv_id, len(evidence_rows)))
    elif match_result.status == "no_matches":
        signals.append(_signal_no_cross_investigation(inv_id, match_result.query_attributes))
    else:
        # "ok" — convert hits to signals
        signals.extend(_signals_from_hits(inv_id, match_result.hits))

    return signals, len(evidence_rows)


def _build_summary(inv_id: int, signals: List[IntelligenceSignal], evidence_count: int) -> str:
    """Build a one-sentence plain-English summary of the intelligence result."""
    cross_matches = [s for s in signals if s.signal_type == SIGNAL_CROSS_INVESTIGATION_MATCH]
    repeated = [s for s in signals if s.signal_type == SIGNAL_REPEATED_ATTRIBUTE]
    high_conf = [s for s in signals if s.signal_type == SIGNAL_HIGH_CONFIDENCE_EVIDENCE]

    if evidence_count == 0:
        return "No evidence has been recorded for this investigation."

    if not cross_matches and not repeated:
        if high_conf:
            return (
                f"Investigation has {evidence_count} evidence item(s) with "
                f"{len(high_conf)} high-confidence item(s); "
                "no cross-investigation matches found."
            )
        return (
            f"Investigation has {evidence_count} evidence item(s); "
            "no cross-investigation matches found."
        )

    parts = []
    if cross_matches:
        # Count distinct matched investigations
        inv_set = {i for s in cross_matches for i in s.investigation_ids if i != inv_id}
        parts.append(
            f"matches evidence in {len(inv_set)} other investigation(s) "
            f"across {len(cross_matches)} attribute type(s)"
        )
    if repeated:
        parts.append(
            f"{len(repeated)} attribute(s) appear in 3+ investigations"
        )

    return (
        f"Investigation has {evidence_count} evidence item(s); "
        + "; ".join(parts) + "."
    )


def build_intelligence(inv_id: int, db: Session) -> IntelligenceResult:
    """
    Build the complete intelligence result for the given investigation.

    Args:
        inv_id: The ID of the already-verified Investigation.
        db:     Active SQLAlchemy session.

    Returns:
        IntelligenceResult with deterministic signals.
        provider="deterministic" — no AI/LLM involved.
    """
    signals, evidence_count = _run_deterministic_analysis(inv_id, db)
    summary = _build_summary(inv_id, signals, evidence_count)

    return IntelligenceResult(
        investigation_id=inv_id,
        signals=signals,
        summary=summary,
        total_evidence=evidence_count,
        total_signals=len(signals),
        provider="deterministic",
        generated_at=datetime.utcnow(),
    )
