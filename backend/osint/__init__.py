"""TraceX OSINT provider package (Chunk 8 Phase A).

Required providers:
    dns     — dnspython
    whois   — python-whois

Optional CLI providers (not Python dependencies; TraceX stays up if missing):
    theharvester — allowlisted `theHarvester` / `theharvester` executable on PATH
    sherlock     — allowlisted `sherlock` executable on PATH
"""

from .registry import ProviderRegistry, build_default_registry, default_provider_names
from .types import ProviderResult

__all__ = [
    "ProviderRegistry",
    "ProviderResult",
    "build_default_registry",
    "default_provider_names",
]
