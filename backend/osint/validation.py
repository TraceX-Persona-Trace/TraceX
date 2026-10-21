"""Target validation for public OSINT lookups.

Rejects private, local, malformed, and injection-prone inputs.
Does not fetch or invent data.
"""
from __future__ import annotations

import ipaddress
import re
from typing import Optional


class InvalidTargetError(ValueError):
    """Raised when a lookup target is not a safe public identifier."""


# At least two labels; TLD letters or punycode. No underscores, spaces, or paths.
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:[a-z]{2,63}|xn--[a-z0-9-]{2,59})$"
)

_USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,62}[A-Za-z0-9])?$")

_BLOCKED_DOMAIN_SUFFIXES = frozenset(
    {
        "local",
        "localhost",
        "internal",
        "intranet",
        "lan",
        "home",
        "corp",
        "private",
        "localdomain",
        "invalid",
        "onion",
    }
)

_BLOCKED_HOSTS = frozenset({"localhost", "localhost.localdomain"})


def _looks_like_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def normalize_public_domain(raw: str) -> str:
    """Return a canonical public domain or raise InvalidTargetError."""
    if raw is None:
        raise InvalidTargetError("Domain is required")
    if not isinstance(raw, str):
        raise InvalidTargetError("Domain must be a string")

    candidate = raw.strip().strip(".").lower()
    if not candidate:
        raise InvalidTargetError("Domain is required")

    if any(ch.isspace() for ch in candidate):
        raise InvalidTargetError("Domain must not contain whitespace")

    if "://" in candidate or "/" in candidate or "\\" in candidate:
        raise InvalidTargetError("Domain must not be a URL or path")

    if any(ch in candidate for ch in ("?", "#", "@", ",", ";", "|", "&", "=", "%", "'", '"', "`")):
        raise InvalidTargetError("Domain contains disallowed characters")

    if _looks_like_ip(candidate):
        raise InvalidTargetError("IP addresses are not accepted as domain targets")

    try:
        candidate = candidate.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError) as exc:
        raise InvalidTargetError("Domain is not a valid IDNA hostname") from exc

    if not _DOMAIN_RE.fullmatch(candidate):
        raise InvalidTargetError("Domain is not a valid public hostname")

    if candidate in _BLOCKED_HOSTS:
        raise InvalidTargetError("Local hostnames are not public lookup targets")

    tld = candidate.rsplit(".", 1)[-1]
    if tld in _BLOCKED_DOMAIN_SUFFIXES:
        raise InvalidTargetError("Non-public or reserved domains are not allowed")

    labels = candidate.split(".")
    if any(label.startswith("-") or label.endswith("-") for label in labels):
        raise InvalidTargetError("Domain labels must not start or end with a hyphen")

    return candidate


def normalize_public_username(raw: str) -> str:
    """Return a canonical public username or raise InvalidTargetError."""
    if raw is None:
        raise InvalidTargetError("Username is required")
    if not isinstance(raw, str):
        raise InvalidTargetError("Username must be a string")

    candidate = raw.strip()
    if not candidate:
        raise InvalidTargetError("Username is required")

    if any(ch.isspace() for ch in candidate):
        raise InvalidTargetError("Username must not contain whitespace")

    if candidate.startswith("@"):
        candidate = candidate[1:]

    lowered = candidate.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        raise InvalidTargetError("Username must not be a URL")

    if any(ch in candidate for ch in ("/", "\\", "?", "#", "@", ",", ";", "|", "&", "=", "%", "'", '"', "`")):
        raise InvalidTargetError("Username contains disallowed characters")

    if not _USERNAME_RE.fullmatch(candidate):
        raise InvalidTargetError("Username is not a valid public handle")

    if len(candidate) > 64:
        raise InvalidTargetError("Username exceeds maximum length")

    return candidate


def validation_error_message(exc: BaseException) -> Optional[str]:
    text = str(exc).strip()
    return text or "Invalid target"
