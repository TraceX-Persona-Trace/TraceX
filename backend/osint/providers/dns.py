"""DNS provider using dnspython. Public domains only. No fabricated records."""
from __future__ import annotations

from typing import Any, Iterable, List, Optional

import dns.exception
import dns.resolver

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

DEFAULT_RECORD_TYPES: tuple[str, ...] = ("A", "AAAA", "MX", "NS", "TXT")
DEFAULT_TIMEOUT = 8.0


class DnsProvider(OsintProvider):
    name = "dns"
    supported_target_types = frozenset({TARGET_TYPE_DOMAIN})
    optional = False
    description = "Public DNS lookup for A, AAAA, MX, NS, and TXT records."

    def __init__(
        self,
        resolver: Any = None,
        record_types: Iterable[str] = DEFAULT_RECORD_TYPES,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._resolver = resolver
        self._record_types = tuple(record_types)
        self._timeout = timeout

    def validate_target(self, target: str, target_type: str) -> str:
        require_target_type(self.supported_target_types, target_type)
        return normalize_public_domain(target)

    def _resolver_instance(self) -> Any:
        if self._resolver is not None:
            return self._resolver
        resolver = dns.resolver.Resolver()
        resolver.lifetime = self._timeout
        resolver.timeout = self._timeout
        return resolver

    def run(self, target: str, target_type: str) -> ProviderResult:
        resolver = self._resolver_instance()
        findings: List[OsintFinding] = []
        queried: List[str] = []
        timed_out = False
        lookup_error: Optional[str] = None

        for rdtype in self._record_types:
            queried.append(rdtype)
            try:
                answer = resolver.resolve(target, rdtype)
            except dns.resolver.NXDOMAIN:
                lookup_error = "NXDOMAIN"
                break
            except dns.resolver.NoAnswer:
                continue
            except dns.resolver.NoNameservers as exc:
                lookup_error = f"NoNameservers: {exc}"
                continue
            except dns.exception.Timeout:
                timed_out = True
                continue
            except Exception as exc:  # noqa: BLE001
                lookup_error = type(exc).__name__
                continue

            parsed = _parse_records(rdtype, answer)
            findings.extend(parsed)

        if findings:
            return ProviderResult(
                provider=self.name,
                status=STATUS_OK,
                target=target,
                target_type=target_type,
                findings=findings,
                meta={"record_types": queried},
            )

        if timed_out and lookup_error is None:
            return ProviderResult(
                provider=self.name,
                status=STATUS_TIMEOUT,
                target=target,
                target_type=target_type,
                error="DNS lookup timed out",
                meta={"record_types": queried},
            )

        if lookup_error == "NXDOMAIN":
            return ProviderResult(
                provider=self.name,
                status=STATUS_EMPTY,
                target=target,
                target_type=target_type,
                error="Domain has no DNS records (NXDOMAIN)",
                meta={"record_types": queried},
            )

        if lookup_error:
            return ProviderResult(
                provider=self.name,
                status=STATUS_LOOKUP_FAILED,
                target=target,
                target_type=target_type,
                error=lookup_error,
                meta={"record_types": queried},
            )

        return ProviderResult(
            provider=self.name,
            status=STATUS_EMPTY,
            target=target,
            target_type=target_type,
            error="No DNS records returned",
            meta={"record_types": queried},
        )


def _parse_records(rdtype: str, answer: Any) -> List[OsintFinding]:
    findings: List[OsintFinding] = []
    rdtype_upper = rdtype.upper()
    for record in answer:
        parsed = _parse_one(rdtype_upper, record)
        if parsed is not None:
            findings.append(parsed)
    return findings


def _parse_one(rdtype: str, record: Any) -> Optional[OsintFinding]:
    if rdtype in {"A", "AAAA"}:
        address = getattr(record, "address", None)
        if not address:
            return None
        return OsintFinding(
            finding_type=f"dns_{rdtype.lower()}",
            value=str(address),
            details={"record_type": rdtype},
        )

    if rdtype == "MX":
        exchange = _name_to_text(getattr(record, "exchange", None))
        if not exchange:
            return None
        preference = getattr(record, "preference", None)
        details = {"record_type": "MX"}
        if preference is not None:
            details["preference"] = int(preference)
        return OsintFinding(finding_type="dns_mx", value=exchange.rstrip("."), details=details)

    if rdtype == "NS":
        target = _name_to_text(getattr(record, "target", None))
        if not target:
            return None
        return OsintFinding(
            finding_type="dns_ns",
            value=target.rstrip("."),
            details={"record_type": "NS"},
        )

    if rdtype == "TXT":
        text = _txt_to_text(record)
        if not text:
            return None
        return OsintFinding(
            finding_type="dns_txt",
            value=text,
            details={"record_type": "TXT"},
        )

    rendered = str(record).strip()
    if not rendered:
        return None
    return OsintFinding(
        finding_type=f"dns_{rdtype.lower()}",
        value=rendered,
        details={"record_type": rdtype},
    )


def _name_to_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "to_text"):
        text = value.to_text()
        return str(text) if text else None
    text = str(value).strip()
    return text or None


def _txt_to_text(record: Any) -> Optional[str]:
    strings = getattr(record, "strings", None)
    if strings:
        parts: List[str] = []
        for chunk in strings:
            if isinstance(chunk, bytes):
                parts.append(chunk.decode("utf-8", errors="replace"))
            else:
                parts.append(str(chunk))
        joined = "".join(parts).strip()
        return joined or None
    text = getattr(record, "to_text", lambda: str(record))()
    text = str(text).strip().strip('"')
    return text or None
