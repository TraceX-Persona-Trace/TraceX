"""OSINT lookup orchestration and Evidence ingestion (Chunk 8 Phase B).

Uses Phase A providers as-is. Persists successful findings through the existing
Evidence model — the same columns as manual evidence create. Failed, empty,
unavailable, timeout, malformed, and error results are returned but not stored.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from models.evidence import Evidence
from models.investigation import Investigation
from osint.registry import ProviderRegistry, build_default_registry
from osint.types import (
    STATUS_OK,
    TARGET_TYPE_DOMAIN,
    TARGET_TYPE_USERNAME,
    OsintFinding,
    ProviderResult,
)
from osint.validation import (
    InvalidTargetError,
    normalize_public_domain,
    normalize_public_username,
)
from schemas.evidence import VALID_EVIDENCE_TYPES

# Only STATUS_OK findings are ingested. Other statuses stay in the API payload.
INGESTIBLE_STATUSES = frozenset({STATUS_OK})

# Maps Phase A finding_type → existing Evidence.evidence_type.
# Unlisted types fall back to "other".
_FINDING_TO_EVIDENCE_TYPE = {
    "dns_a": "ip_address",
    "dns_aaaa": "ip_address",
    "dns_mx": "domain",
    "dns_ns": "domain",
    "dns_txt": "other",
    "whois_domain_name": "domain",
    "whois_emails": "email",
    "whois_name_servers": "domain",
    "email": "email",
    "host": "domain",
    "ip_address": "ip_address",
    "social_profile": "social_profile",
    "username": "username",
}

_MATCHABLE_TYPES = frozenset({"email", "phone", "username", "domain", "ip_address"})


def validate_osint_target(target: str, target_type: str) -> Tuple[str, str]:
    """Apply Phase A public-target rules. Raises InvalidTargetError."""
    if target_type == TARGET_TYPE_DOMAIN:
        return normalize_public_domain(target), TARGET_TYPE_DOMAIN
    if target_type == TARGET_TYPE_USERNAME:
        return normalize_public_username(target), TARGET_TYPE_USERNAME
    raise InvalidTargetError("target_type must be 'domain' or 'username'")


def providers_for_target_type(registry: ProviderRegistry, target_type: str) -> List:
    return [provider for provider in registry.all() if provider.supports(target_type)]


def evidence_type_for_finding(finding_type: str) -> str:
    mapped = _FINDING_TO_EVIDENCE_TYPE.get(finding_type, "other")
    if mapped not in VALID_EVIDENCE_TYPES:
        return "other"
    return mapped


def normalised_value_for_finding(evidence_type: str, value: str, finding: OsintFinding) -> Optional[str]:
    text = (value or "").strip()
    if not text:
        return None
    if evidence_type == "email":
        return text.lower()
    if evidence_type == "domain":
        return text.rstrip(".").lower()
    if evidence_type == "ip_address":
        return text
    if evidence_type == "username":
        return text
    if evidence_type == "social_profile":
        details = finding.details or {}
        username = details.get("username")
        if isinstance(username, str) and username.strip():
            return username.strip()
        return None
    if evidence_type not in _MATCHABLE_TYPES:
        return None
    return text


def _source_url(finding: OsintFinding) -> Optional[str]:
    value = (finding.value or "").strip()
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value
    details = finding.details or {}
    for key in ("url", "source_url"):
        candidate = details.get(key)
        if isinstance(candidate, str):
            parsed = urlparse(candidate.strip())
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                return candidate.strip()
    return None


def _metadata_json(
    result: ProviderResult,
    finding: OsintFinding,
) -> str:
    payload = {
        "provider": result.provider,
        "target": result.target,
        "target_type": result.target_type,
        "finding_type": finding.finding_type,
        "provider_status": result.status,
    }
    if finding.details:
        payload["details"] = finding.details
    return json.dumps(payload, default=str)


def ingest_successful_findings(
    investigation_id: int,
    results: Sequence[ProviderResult],
    db: Session,
) -> List[Evidence]:
    """Insert Evidence rows for STATUS_OK findings only."""
    created: List[Evidence] = []
    for result in results:
        if result.status not in INGESTIBLE_STATUSES:
            continue
        for finding in result.findings:
            if not finding.value or not str(finding.value).strip():
                continue
            evidence_type = evidence_type_for_finding(finding.finding_type)
            value = str(finding.value).strip()
            ev = Evidence(
                investigation_id=investigation_id,
                source_type="osint",
                source_name=result.provider,
                source_url=_source_url(finding),
                title=f"{result.provider}: {finding.finding_type}",
                content=value,
                evidence_type=evidence_type,
                confidence=0.0,
                metadata_json=_metadata_json(result, finding),
                normalised_value=normalised_value_for_finding(evidence_type, value, finding),
            )
            db.add(ev)
            created.append(ev)
    if created:
        db.commit()
        for ev in created:
            db.refresh(ev)
    return created


def run_osint_lookup(
    investigation: Investigation,
    target: str,
    target_type: str,
    db: Session,
    registry: Optional[ProviderRegistry] = None,
) -> Tuple[str, str, List[ProviderResult], List[Evidence]]:
    """
    Validate target, run matching providers, ingest ok findings.

    Returns (normalised_target, target_type, provider_results, created_evidence).
    """
    normalised, resolved_type = validate_osint_target(target, target_type)
    active_registry = registry or build_default_registry()
    selected = providers_for_target_type(active_registry, resolved_type)

    results: List[ProviderResult] = []
    for provider in selected:
        results.append(provider.execute(normalised, resolved_type))

    created = ingest_successful_findings(investigation.id, results, db)
    return normalised, resolved_type, results, created


def public_error_message(exc: BaseException) -> str:
    """Short client-safe error; no traceback."""
    if isinstance(exc, InvalidTargetError):
        text = str(exc).strip()
        return text or "Invalid target"
    return "OSINT lookup failed"
