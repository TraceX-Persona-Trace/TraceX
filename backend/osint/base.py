"""OSINT provider base abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import FrozenSet, Iterable

from .types import (
    STATUS_ERROR,
    STATUS_INVALID_TARGET,
    STATUS_PROVIDER_UNAVAILABLE,
    STATUS_UNSUPPORTED_TARGET,
    ProviderResult,
)
from .validation import InvalidTargetError, validation_error_message


class OsintProvider(ABC):
    """Contract for a single OSINT lookup provider.

    Implementations must not fabricate findings. Missing data is omitted.
    """

    name: str
    supported_target_types: FrozenSet[str]
    optional: bool = False
    description: str = ""

    def supports(self, target_type: str) -> bool:
        return target_type in self.supported_target_types

    def is_available(self) -> bool:
        """Required providers are always available; optional CLIs may not be."""
        return True

    @abstractmethod
    def validate_target(self, target: str, target_type: str) -> str:
        """Return a normalised target or raise InvalidTargetError."""

    @abstractmethod
    def run(self, target: str, target_type: str) -> ProviderResult:
        """Execute a lookup against an already-validated target."""

    def execute(self, target: str, target_type: str) -> ProviderResult:
        """Validate, check availability, and run with controlled errors."""
        if not self.supports(target_type):
            return ProviderResult(
                provider=self.name,
                status=STATUS_UNSUPPORTED_TARGET,
                target=str(target) if target is not None else "",
                target_type=target_type,
                error=f"Provider '{self.name}' does not support target type '{target_type}'",
            )

        try:
            normalised = self.validate_target(target, target_type)
        except InvalidTargetError as exc:
            return ProviderResult(
                provider=self.name,
                status=STATUS_INVALID_TARGET,
                target=str(target) if target is not None else "",
                target_type=target_type,
                error=validation_error_message(exc),
            )

        if not self.is_available():
            return ProviderResult(
                provider=self.name,
                status=STATUS_PROVIDER_UNAVAILABLE,
                target=normalised,
                target_type=target_type,
                error=f"Optional provider '{self.name}' is not installed or not on PATH",
                meta={"optional": True},
            )

        try:
            return self.run(normalised, target_type)
        except Exception as exc:  # noqa: BLE001 — envelope, do not crash caller
            return ProviderResult(
                provider=self.name,
                status=STATUS_ERROR,
                target=normalised,
                target_type=target_type,
                error=_safe_error_message(exc),
            )


def _safe_error_message(exc: BaseException) -> str:
    name = type(exc).__name__
    text = str(exc).strip()
    if not text:
        return name
    return f"{name}: {text[:300]}"


def require_target_type(supported: Iterable[str], target_type: str) -> None:
    if target_type not in set(supported):
        raise InvalidTargetError(f"Unsupported target type '{target_type}'")
