"""WHOIS provider using python-whois. Public domains only. No fabricated fields."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, List, Optional

import whois
from whois.exceptions import WhoisError

from osint.base import OsintProvider, require_target_type
from osint.types import (
    STATUS_EMPTY,
    STATUS_LOOKUP_FAILED,
    STATUS_OK,
    STATUS_TIMEOUT,
    TARGET_TYPE_DOMAIN,
    OsintFinding,
    ProviderResult,
)
from osint.validation import normalize_public_domain

DEFAULT_TIMEOUT = 10

# Public registration fields only. Omitted when the library returns nothing.
_WHOIS_FIELDS = (
    "domain_name",
    "registrar",
    "whois_server",
    "creation_date",
    "expiration_date",
    "updated_date",
    "name_servers",
    "status",
    "emails",
    "org",
    "country",
    "dnssec",
)

LookupFn = Callable[..., Any]


class WhoisProvider(OsintProvider):
    name = "whois"
    supported_target_types = frozenset({TARGET_TYPE_DOMAIN})
    optional = False
    description = "Public WHOIS registration lookup for a domain."

    def __init__(self, lookup_fn: Optional[LookupFn] = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._lookup_fn = lookup_fn or whois.whois
        self._timeout = timeout

    def validate_target(self, target: str, target_type: str) -> str:
        require_target_type(self.supported_target_types, target_type)
        return normalize_public_domain(target)

    def run(self, target: str, target_type: str) -> ProviderResult:
        try:
            raw = self._lookup_fn(target, timeout=self._timeout, quiet=True)
        except TimeoutError:
            return ProviderResult(
                provider=self.name,
                status=STATUS_TIMEOUT,
                target=target,
                target_type=target_type,
                error="WHOIS lookup timed out",
            )
        except WhoisError as exc:
            return ProviderResult(
                provider=self.name,
                status=STATUS_LOOKUP_FAILED,
                target=target,
                target_type=target_type,
                error=_whois_error_text(exc),
            )
        except Exception as exc:  # noqa: BLE001
            if _is_timeout(exc):
                return ProviderResult(
                    provider=self.name,
                    status=STATUS_TIMEOUT,
                    target=target,
                    target_type=target_type,
                    error="WHOIS lookup timed out",
                )
            return ProviderResult(
                provider=self.name,
                status=STATUS_LOOKUP_FAILED,
                target=target,
                target_type=target_type,
                error=f"{type(exc).__name__}: {str(exc)[:300]}".strip(),
            )

        if raw is None:
            return ProviderResult(
                provider=self.name,
                status=STATUS_EMPTY,
                target=target,
                target_type=target_type,
                error="WHOIS returned no data",
            )

        findings = _findings_from_whois(raw)
        if not findings:
            return ProviderResult(
                provider=self.name,
                status=STATUS_EMPTY,
                target=target,
                target_type=target_type,
                error="WHOIS returned no usable registration fields",
            )

        return ProviderResult(
            provider=self.name,
            status=STATUS_OK,
            target=target,
            target_type=target_type,
            findings=findings,
        )


def _is_timeout(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return "timeout" in name or "timed out" in text or "timeout" in text


def _whois_error_text(exc: WhoisError) -> str:
    text = str(exc).strip()
    return text or "WHOIS lookup failed"


def _findings_from_whois(raw: Any) -> List[OsintFinding]:
    findings: List[OsintFinding] = []
    for field_name in _WHOIS_FIELDS:
        value = _get_field(raw, field_name)
        serialised = _serialise(value)
        if serialised is None:
            continue
        if isinstance(serialised, list):
            for item in serialised:
                if item is None or item == "":
                    continue
                findings.append(
                    OsintFinding(
                        finding_type=f"whois_{field_name}",
                        value=str(item),
                        details={"field": field_name},
                    )
                )
        else:
            findings.append(
                OsintFinding(
                    finding_type=f"whois_{field_name}",
                    value=str(serialised),
                    details={"field": field_name},
                )
            )
    return findings


def _get_field(raw: Any, name: str) -> Any:
    if isinstance(raw, dict):
        return raw.get(name)
    return getattr(raw, name, None)


def _serialise(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        items = []
        for item in value:
            serialised = _serialise(item)
            if serialised is None or serialised == "":
                continue
            if isinstance(serialised, list):
                items.extend(serialised)
            else:
                items.append(serialised)
        return items or None
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace").strip()
        return text or None
    text = str(value).strip()
    if not text or text.lower() in {"none", "n/a", "not available", "redacted"}:
        return None
    return text
