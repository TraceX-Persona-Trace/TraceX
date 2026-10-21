"""theHarvester adapter.

Optional CLI. TraceX does not depend on it. If the allowlisted executable is
not on PATH, returns provider_unavailable. Never fabricates findings.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any, List, Optional

from osint.base import OsintProvider, require_target_type
from osint.cli import RunFn, WhichFn, decode_cli_output, resolve_allowlisted_executable, run_allowlisted
from osint.types import (
    STATUS_EMPTY,
    STATUS_LOOKUP_FAILED,
    STATUS_MALFORMED_OUTPUT,
    STATUS_OK,
    STATUS_PROVIDER_UNAVAILABLE,
    STATUS_TIMEOUT,
    TARGET_TYPE_DOMAIN,
    OsintFinding,
    ProviderResult,
)
from osint.validation import normalize_public_domain

ALLOWED_EXECUTABLES = ("theHarvester", "theharvester")
DEFAULT_TIMEOUT = 30.0
# Fixed source — never taken from user input.
ALLOWLISTED_SOURCE = "duckduckgo"
ALLOWLISTED_LIMIT = "50"

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$")
_HOST_RE = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
)


class TheHarvesterProvider(OsintProvider):
    name = "theharvester"
    supported_target_types = frozenset({TARGET_TYPE_DOMAIN})
    optional = True
    description = (
        "Optional theHarvester CLI adapter for public domain harvesting. "
        "Install theHarvester separately and place it on PATH if you want this provider."
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
        if self._executable_path:
            return self._executable_path
        return resolve_allowlisted_executable(ALLOWED_EXECUTABLES, which_fn=self._which_fn)

    def validate_target(self, target: str, target_type: str) -> str:
        require_target_type(self.supported_target_types, target_type)
        return normalize_public_domain(target)

    def run(self, target: str, target_type: str) -> ProviderResult:
        executable = self._resolved_executable()
        if executable is None:
            return ProviderResult(
                provider=self.name,
                status=STATUS_PROVIDER_UNAVAILABLE,
                target=target,
                target_type=target_type,
                error="theHarvester is not installed or not on PATH",
                meta={"optional": True, "allowed_executables": list(ALLOWED_EXECUTABLES)},
            )

        args = ["-d", target, "-l", ALLOWLISTED_LIMIT, "-b", ALLOWLISTED_SOURCE]
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
                error="theHarvester timed out",
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

        parsed = _parse_harvester_output(stdout)
        if parsed.status == "malformed":
            return ProviderResult(
                provider=self.name,
                status=STATUS_MALFORMED_OUTPUT,
                target=target,
                target_type=target_type,
                error="theHarvester output could not be parsed",
                meta={"optional": True},
            )

        findings = parsed.findings
        if not findings:
            return ProviderResult(
                provider=self.name,
                status=STATUS_EMPTY,
                target=target,
                target_type=target_type,
                error="theHarvester returned no public findings",
                meta={"optional": True},
            )

        return ProviderResult(
            provider=self.name,
            status=STATUS_OK,
            target=target,
            target_type=target_type,
            findings=findings,
            meta={"optional": True, "source": ALLOWLISTED_SOURCE},
        )


class _Parsed:
    def __init__(self, findings: List[OsintFinding], status: str) -> None:
        self.findings = findings
        self.status = status  # ok | empty | malformed


def _cli_error(returncode: Any, stderr: str) -> str:
    snippet = (stderr or "").strip().splitlines()
    tail = snippet[-1] if snippet else ""
    if tail:
        return f"theHarvester exited with code {returncode}: {tail[:200]}"
    return f"theHarvester exited with code {returncode}"


def _parse_harvester_output(stdout: str) -> _Parsed:
    text = (stdout or "").strip()
    if not text:
        return _Parsed([], "empty")

    json_payload = _extract_json_object(text)
    if json_payload is not None:
        findings = _findings_from_json(json_payload)
        return _Parsed(findings, "ok")

    findings = _findings_from_text(text)
    if findings:
        return _Parsed(findings, "ok")

    if _looks_like_harvester_empty(text):
        return _Parsed([], "empty")

    return _Parsed([], "malformed")


def _extract_json_object(text: str) -> Optional[Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        start_l = text.find("[")
        end_l = text.rfind("]")
        if start_l == -1 or end_l == -1 or end_l <= start_l:
            return None
        blob = text[start_l : end_l + 1]
    else:
        blob = text[start : end + 1]
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


def _findings_from_json(payload: Any) -> List[OsintFinding]:
    findings: List[OsintFinding] = []
    if isinstance(payload, list):
        for item in payload:
            findings.extend(_findings_from_json(item))
        return findings
    if not isinstance(payload, dict):
        return findings

    emails = payload.get("emails") or payload.get("email") or []
    hosts = payload.get("hosts") or payload.get("host") or []
    ips = payload.get("ips") or payload.get("ip") or []

    for email in _as_list(emails):
        if _EMAIL_RE.fullmatch(email):
            findings.append(OsintFinding(finding_type="email", value=email.lower()))
    for host in _as_list(hosts):
        host_n = host.strip().rstrip(".").lower()
        if _HOST_RE.fullmatch(host_n):
            findings.append(OsintFinding(finding_type="host", value=host_n))
    for ip in _as_list(ips):
        ip_n = ip.strip()
        if ip_n:
            findings.append(OsintFinding(finding_type="ip_address", value=ip_n))
    return findings


def _findings_from_text(text: str) -> List[OsintFinding]:
    findings: List[OsintFinding] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("[*]"):
            continue
        if _EMAIL_RE.fullmatch(line):
            findings.append(OsintFinding(finding_type="email", value=line.lower()))
            continue
        host = line.rstrip(".").lower()
        if _HOST_RE.fullmatch(host) and "." in host:
            findings.append(OsintFinding(finding_type="host", value=host))
    return findings


def _looks_like_harvester_empty(text: str) -> bool:
    lowered = text.lower()
    return "no emails found" in lowered or "no hosts found" in lowered or "0 emails" in lowered


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        out = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    return []
