"""Sherlock adapter.

Optional CLI. TraceX does not depend on it. If the allowlisted executable is
not on PATH, returns provider_unavailable. Never fabricates profile hits.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any, List, Optional
from urllib.parse import urlparse

from ..base import OsintProvider, require_target_type
from ..cli import RunFn, WhichFn, decode_cli_output, resolve_allowlisted_executable, run_allowlisted
from ..types import (
    STATUS_EMPTY,
    STATUS_LOOKUP_FAILED,
    STATUS_MALFORMED_OUTPUT,
    STATUS_OK,
    STATUS_PROVIDER_UNAVAILABLE,
    STATUS_TIMEOUT,
    TARGET_TYPE_USERNAME,
    OsintFinding,
    ProviderResult,
)
from ..validation import normalize_public_username

ALLOWED_EXECUTABLES = ("sherlock",)
DEFAULT_TIMEOUT = 120.0

_POSITIVE_STATUSES = frozenset({"claimed", "available", "found"})
_NEGATIVE_STATUSES = frozenset(
    {"illegal", "unknown", "waf", "blocked", "error", "false", "not found", "notfound"}
)
# Sherlock text hits typically look like: [+] GitHub: https://github.com/user
_TEXT_HIT_RE = re.compile(r"^\[\+\]\s+(.+?):\s+(\S+)$")


class SherlockProvider(OsintProvider):
    name = "sherlock"
    supported_target_types = frozenset({TARGET_TYPE_USERNAME})
    optional = True
    description = (
        "Optional Sherlock CLI adapter for public username availability checks. "
        "Install Sherlock separately and place it on PATH if you want this provider."
    )

    def __init__(
        self,
        which_fn: WhichFn = shutil.which,
        run_fn: RunFn = subprocess.run,
        timeout: float = DEFAULT_TIMEOUT,
        executable_path: Optional[str] = None,
    ) -> None:
        self._which_fn = which_fn
        self._run_fn = run_fn
        self._timeout = timeout
        self._executable_path = executable_path

    def is_available(self) -> bool:
        return self._resolved_executable() is not None

    def _resolved_executable(self) -> Optional[str]:
        # First, use any explicitly supplied path
        if self._executable_path:
            return self._executable_path
        # If a custom which_fn is provided (e.g., for testing), rely on it without venv shortcuts
        import shutil
        if self._which_fn is not shutil.which:
            return resolve_allowlisted_executable(ALLOWED_EXECUTABLES, which_fn=self._which_fn)
        # Default behavior: try to locate the executable in the active virtual environment's Scripts directory
        try:
            import os, sys
            venv_dir = os.path.dirname(sys.executable)
            candidate = os.path.join(venv_dir, "sherlock.exe")
            if os.path.isfile(candidate):
                return candidate
        except Exception:
            pass
        # Fall back to a standard PATH lookup for allowed executables
        return resolve_allowlisted_executable(ALLOWED_EXECUTABLES, which_fn=self._which_fn)

    def validate_target(self, target: str, target_type: str) -> str:
        require_target_type(self.supported_target_types, target_type)
        return normalize_public_username(target)

    def run(self, target: str, target_type: str) -> ProviderResult:
        executable = self._resolved_executable()
        if executable is None:
            return ProviderResult(
                provider=self.name,
                status=STATUS_PROVIDER_UNAVAILABLE,
                target=target,
                target_type=target_type,
                error="Sherlock is not installed or not on PATH",
                meta={"optional": True, "allowed_executables": list(ALLOWED_EXECUTABLES)},
            )

        # Fixed flags only. Username is a validated positional argument.
        args = ["--print-found", "--timeout", "30", "--no-color", target]
        try:
            completed = run_allowlisted(
                executable,
                args,
                timeout=self._timeout,
                run_fn=self._run_fn,
            )
        except subprocess.TimeoutExpired:
            return ProviderResult(
                provider=self.name,
                status=STATUS_TIMEOUT,
                target=target,
                target_type=target_type,
                error="Sherlock timed out",
                meta={"optional": True},
            )

        stdout, stderr = decode_cli_output(completed)
        if completed.returncode not in (0, None) and not stdout.strip():
            return ProviderResult(
                provider=self.name,
                status=STATUS_LOOKUP_FAILED,
                target=target,
                target_type=target_type,
                error=_cli_error(completed.returncode, stderr),
                meta={"optional": True, "returncode": completed.returncode},
            )

        parsed = _parse_sherlock_output(stdout, target)
        if parsed.status == "malformed":
            return ProviderResult(
                provider=self.name,
                status=STATUS_MALFORMED_OUTPUT,
                target=target,
                target_type=target_type,
                error="Sherlock output could not be parsed",
                meta={"optional": True},
            )

        if not parsed.findings:
            return ProviderResult(
                provider=self.name,
                status=STATUS_EMPTY,
                target=target,
                target_type=target_type,
                error="Sherlock returned no public profile hits",
                meta={"optional": True},
            )

        return ProviderResult(
            provider=self.name,
            status=STATUS_OK,
            target=target,
            target_type=target_type,
            findings=parsed.findings,
            meta={"optional": True},
        )


class _Parsed:
    def __init__(self, findings: List[OsintFinding], status: str) -> None:
        self.findings = findings
        self.status = status


def _cli_error(returncode: Any, stderr: str) -> str:
    snippet = (stderr or "").strip().splitlines()
    tail = snippet[-1] if snippet else ""
    if tail:
        return f"Sherlock exited with code {returncode}: {tail[:200]}"
    return f"Sherlock exited with code {returncode}"


def _parse_sherlock_output(stdout: str, username: str) -> _Parsed:
    text = (stdout or "").strip()
    if not text:
        return _Parsed([], "empty")

    json_payload = _extract_json(text)
    if json_payload is not None:
        findings = _findings_from_json(json_payload, username)
        return _Parsed(findings, "ok")

    findings = _findings_from_text(text)
    if findings:
        return _Parsed(findings, "ok")

    if _looks_like_sherlock_empty(text):
        return _Parsed([], "empty")

    return _Parsed([], "malformed")


def _extract_json(text: str) -> Optional[Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def _findings_from_json(payload: dict, username: str) -> List[OsintFinding]:
    findings: List[OsintFinding] = []
    for site, info in payload.items():
        if not isinstance(site, str):
            continue
        url = None
        status = None
        if isinstance(info, str):
            url = info
        elif isinstance(info, dict):
            url = info.get("url") or info.get("url_user") or info.get("link")
            status = info.get("status") or info.get("status_code")
            if isinstance(status, dict):
                status = status.get("status")
        else:
            continue

        if status is not None:
            status_text = str(status).strip().lower()
            if status_text in _NEGATIVE_STATUSES:
                continue
            if status_text not in _POSITIVE_STATUSES:
                continue

        if not url or not isinstance(url, str):
            continue
        if not _is_http_url(url):
            continue
        findings.append(
            OsintFinding(
                finding_type="social_profile",
                value=url.strip(),
                details={"site": site, "username": username},
            )
        )
    return findings


def _findings_from_text(text: str) -> List[OsintFinding]:
    findings: List[OsintFinding] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = _TEXT_HIT_RE.match(line)
        if not match:
            continue
        site, url = match.group(1).strip(), match.group(2).strip()
        if not _is_http_url(url):
            continue
        findings.append(
            OsintFinding(
                finding_type="social_profile",
                value=url,
                details={"site": site},
            )
        )
    return findings


def _looks_like_sherlock_empty(text: str) -> bool:
    lowered = text.lower()
    return "no results found" in lowered or "0 accounts found" in lowered


def _is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
