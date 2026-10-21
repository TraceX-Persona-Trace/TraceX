"""Structured OSINT provider result types.

All providers return these types. Missing data is omitted, never invented.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


TARGET_TYPE_DOMAIN = "domain"
TARGET_TYPE_USERNAME = "username"

STATUS_OK = "ok"
STATUS_EMPTY = "empty"
STATUS_INVALID_TARGET = "invalid_target"
STATUS_LOOKUP_FAILED = "lookup_failed"
STATUS_TIMEOUT = "timeout"
STATUS_PROVIDER_UNAVAILABLE = "provider_unavailable"
STATUS_MALFORMED_OUTPUT = "malformed_output"
STATUS_UNSUPPORTED_TARGET = "unsupported_target"
STATUS_ERROR = "error"


@dataclass(frozen=True)
class OsintFinding:
    """One public-information finding produced by a provider."""

    finding_type: str
    value: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ProviderResult:
    """Uniform result envelope for every OSINT provider."""

    provider: str
    status: str
    target: str
    target_type: str
    findings: List[OsintFinding] = field(default_factory=list)
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "target": self.target,
            "target_type": self.target_type,
            "findings": [
                {
                    "finding_type": f.finding_type,
                    "value": f.value,
                    "details": f.details,
                }
                for f in self.findings
            ],
            "error": self.error,
            "meta": self.meta,
        }


@dataclass(frozen=True)
class ProviderInfo:
    name: str
    supported_target_types: List[str]
    available: bool
    optional: bool
    description: str
