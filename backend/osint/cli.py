"""Allowlisted subprocess helpers for optional OSINT CLI tools.

Never uses shell=True. Never interpolates unvalidated user input into flags.
Executable names must match a fixed allowlist (basename only).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import Callable, Optional, Sequence, Tuple

WhichFn = Callable[[str], Optional[str]]
RunFn = Callable[..., subprocess.CompletedProcess]


_SAFE_EXEC_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def resolve_allowlisted_executable(
    allowed_names: Sequence[str],
    which_fn: WhichFn = shutil.which,
) -> Optional[str]:
    """Return the first PATH hit whose basename is in the allowlist."""
    allowed_lower = {name.lower() for name in allowed_names if _SAFE_EXEC_NAME.fullmatch(name)}
    if not allowed_lower:
        return None

    for name in allowed_names:
        if name.lower() not in allowed_lower:
            continue
        path = which_fn(name)
        if not path or not isinstance(path, str):
            continue
        base = os.path.basename(path)
        stem, _ext = os.path.splitext(base)
        if stem.lower() in allowed_lower:
            return path
    return None


def run_allowlisted(
    executable_path: str,
    args: Sequence[str],
    *,
    timeout: float,
    run_fn: RunFn = subprocess.run,
) -> subprocess.CompletedProcess:
    """Run a previously resolved allowlisted executable with fixed args."""
    argv = [executable_path, *args]
    return run_fn(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
        check=False,
    )


def decode_cli_output(completed: subprocess.CompletedProcess) -> Tuple[str, str]:
    stdout = completed.stdout if isinstance(completed.stdout, str) else ""
    stderr = completed.stderr if isinstance(completed.stderr, str) else ""
    return stdout, stderr
