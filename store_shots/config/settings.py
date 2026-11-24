"""Immutable configuration for a store-shots run."""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.models import DeviceType, PlatformSpec
from ..flows import CaptureFlow

_NATIVE_PORTS = {8081, 19000, 19001, 19002, 19003}


@dataclass(frozen=True)
class Settings:
    """All inputs to a capture run, validated once at construction."""

    host: str = "127.0.0.1"
    port: int = 19006
    output_dir: str | Path = "store-assets"
    scheme: str = "http"
    base_path: str = ""
    platforms: tuple[PlatformSpec, ...] = ()
    devices: tuple[str, ...] | None = None
    variants: tuple[str, ...] | None = None
    recommended_only: bool = False
    routes: tuple[str, ...] | None = None
    flows: tuple[CaptureFlow, ...] | None = None
    wait_for_text: str | None = None
    wait_ms: int = 700
    max_routes: int = 25
    max_depth: int = 3
    exclude: tuple[str, ...] = ()
    navigation_timeout_ms: int = 30000
    wait_for_selector: str | None = None
    network_idle: bool = True
    headless: bool = True
    browser_channel: str | None = None
    overwrite: bool = False
    dry_run: bool = False
    dpr_override: int | None = None
    click_buttons: bool = True
    max_actions_per_screen: int = 24
    screens: int | None = None
    min_screenshots: int | None = None
    max_screenshots: int | None = None
    wait_for_loading: bool = True
    dom_quiet_ms: int = 250
    progress: Any | None = None
    # Kept only for backwards compatibility; full-page expansion was removed.
    full_page: str = "never"
    full_page_fit: str = "stretch"

    def __post_init__(self) -> None:
        object.__setattr__(self, "port", int(self.port))
        object.__setattr__(self, "base_path", self.base_path.strip("/"))
        object.__setattr__(self, "max_actions_per_screen", max(1, self.max_actions_per_screen))
        object.__setattr__(self, "dom_quiet_ms", max(0, self.dom_quiet_ms))

        for name in ("screens", "min_screenshots", "max_screenshots"):
            value = getattr(self, name)
            if value is not None and value < 1:
                raise ValueError(f"{name} must be at least 1")
        if (
            self.screens is None
            and self.min_screenshots is not None
            and self.max_screenshots is not None
            and self.min_screenshots > self.max_screenshots
        ):
            raise ValueError("min_screenshots cannot be greater than max_screenshots")

        if self.port in _NATIVE_PORTS:
            warnings.warn(
                f"Port {self.port} is usually Expo's native dev server, not the web server. "
                "If this port is serving the web bundle (platform=web), this warning can be ignored.",
                stacklevel=2,
            )

    @property
    def base_url(self) -> str:
        base = f"{self.scheme}://{self.host}:{self.port}"
        return f"{base}/{self.base_path}" if self.base_path else base

    @property
    def min_screenshots_effective(self) -> int | None:
        return self.screens if self.screens is not None else self.min_screenshots

    @property
    def max_screenshots_effective(self) -> int | None:
        return self.screens if self.screens is not None else self.max_screenshots

    def min_for(self, device: DeviceType) -> int:
        return max(1, self.min_screenshots_effective or device.min_screenshots)

    def max_for(self, device: DeviceType) -> int:
        return max(1, self.max_screenshots_effective or device.max_screenshots)

    def dpr_for(self, device: DeviceType) -> int:
        return self.dpr_override or device.css_dpr


def build_settings(
    host: str = "127.0.0.1",
    port: int = 19006,
    output_dir: str | Path = "store-assets",
    *,
    scheme: str = "http",
    base_path: str = "",
    platforms: Iterable[PlatformSpec] = (),
    devices: Iterable[str] | None = None,
    variants: Iterable[str] | None = None,
    recommended_only: bool = False,
    routes: Iterable[str] | None = None,
    flows: Iterable[CaptureFlow] | None = None,
    wait_for_text: str | None = None,
    wait_ms: int = 700,
    max_routes: int = 25,
    max_depth: int = 3,
    exclude: Iterable[str] = (),
    navigation_timeout_ms: int = 30000,
    wait_for_selector: str | None = None,
    network_idle: bool = True,
    headless: bool = True,
    browser_channel: str | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    dpr_override: int | None = None,
    click_buttons: bool = True,
    max_actions_per_screen: int = 24,
    screens: int | None = None,
    min_screenshots: int | None = None,
    max_screenshots: int | None = None,
    wait_for_loading: bool = True,
    dom_quiet_ms: int = 250,
    progress: Any | None = None,
    full_page: str = "never",
    full_page_fit: str = "stretch",
) -> Settings:
    """Build validated settings; also used by the backwards-compatible facade."""
    return Settings(
        host=host,
        port=port,
        output_dir=output_dir,
        scheme=scheme,
        base_path=base_path,
        platforms=tuple(platforms),
        devices=None if devices is None else tuple(devices),
        variants=None if variants is None else tuple(variants),
        recommended_only=recommended_only,
        routes=None if routes is None else tuple(routes),
        flows=None if flows is None else tuple(flows),
        wait_for_text=wait_for_text,
        wait_ms=wait_ms,
        max_routes=max_routes,
        max_depth=max_depth,
        exclude=tuple(exclude),
        navigation_timeout_ms=navigation_timeout_ms,
        wait_for_selector=wait_for_selector,
        network_idle=network_idle,
        headless=headless,
        browser_channel=browser_channel,
        overwrite=overwrite,
        dry_run=dry_run,
        dpr_override=dpr_override,
        click_buttons=click_buttons,
        max_actions_per_screen=max_actions_per_screen,
        screens=screens,
        min_screenshots=min_screenshots,
        max_screenshots=max_screenshots,
        wait_for_loading=wait_for_loading,
        dom_quiet_ms=dom_quiet_ms,
        progress=progress,
        full_page=full_page,
        full_page_fit=full_page_fit,
    )
