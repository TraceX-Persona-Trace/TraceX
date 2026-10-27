"""Provider registration and discovery."""
from __future__ import annotations

from typing import Dict, List, Optional, Type

from .base import OsintProvider
from .providers.dns import DnsProvider
from .providers.harvester import TheHarvesterProvider
from .providers.sherlock import SherlockProvider
from .providers.whois import WhoisProvider
from .types import ProviderInfo

_DEFAULT_FACTORIES: Dict[str, Type[OsintProvider]] = {
    "dns": DnsProvider,
    "whois": WhoisProvider,
    "theharvester": TheHarvesterProvider,
    "sherlock": SherlockProvider,
}


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, OsintProvider] = {}

    def register(self, provider: OsintProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[OsintProvider]:
        return self._providers.get(name)

    def names(self) -> List[str]:
        return sorted(self._providers)

    def all(self) -> List[OsintProvider]:
        return [self._providers[name] for name in self.names()]

    def infos(self) -> List[ProviderInfo]:
        infos = []
        for provider in self.all():
            infos.append(
                ProviderInfo(
                    name=provider.name,
                    supported_target_types=sorted(provider.supported_target_types),
                    available=provider.is_available(),
                    optional=provider.optional,
                    description=provider.description,
                )
            )
        return infos


def build_default_registry(
    *,
    dns: Optional[OsintProvider] = None,
    whois: Optional[OsintProvider] = None,
    theharvester: Optional[OsintProvider] = None,
    sherlock: Optional[OsintProvider] = None,
) -> ProviderRegistry:
    """Build the standard Phase A registry.

    Optional constructor args exist so tests can inject fakes without network.
    """
    registry = ProviderRegistry()
    registry.register(dns or DnsProvider())
    registry.register(whois or WhoisProvider())
    registry.register(theharvester or TheHarvesterProvider())
    registry.register(sherlock or SherlockProvider())
    return registry


def default_provider_names() -> List[str]:
    return sorted(_DEFAULT_FACTORIES)
