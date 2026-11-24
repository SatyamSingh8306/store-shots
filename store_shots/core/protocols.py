"""Interfaces between the library's layers."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from playwright.sync_api import Browser, Page

from ..flows import CaptureFlow
from .models import DeviceType, ExtraAsset, PlatformSpec, Variant


@runtime_checkable
class ProgressReporter(Protocol):
    """Receives stage updates and completion ticks."""

    def update(self, text: str) -> None: ...

    def tick(self, count: int = 1) -> None: ...

    def finish(self, text: str | None = None) -> None: ...

    def fail(self, message: str) -> None: ...


class PageSettler(Protocol):
    """Waits until a page is fully rendered."""

    def settle(self, page: Page, *, network_idle_timeout_ms: int = 8000) -> None: ...


class ScreenDiscoverer(Protocol):
    """Finds screens to capture."""

    def discover(self, browser: Browser) -> list[CaptureFlow]: ...


class Capturer(Protocol):
    """Captures one screen or extra asset."""

    def capture(
        self,
        *,
        browser: Browser,
        platform: PlatformSpec,
        url: str,
        shot: dict[str, Any],
        shot_index: int,
        device: DeviceType,
        variant: Variant,
    ) -> tuple[dict[str, Any], list[Any]]: ...

    def capture_asset(
        self,
        *,
        browser: Browser,
        platform: PlatformSpec,
        url: str,
        shot: dict[str, Any],
        asset: ExtraAsset,
        device: DeviceType | None,
    ) -> tuple[dict[str, Any], list[Any]]: ...

    def css_viewport(
        self, device: DeviceType, variant: Variant, dpr: int | None = None
    ) -> dict[str, int]: ...
