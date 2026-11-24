"""Backwards-compatible facade over the store-shots services."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .config.settings import Settings, build_settings
from .core.models import PlatformSpec
from .flows import CaptureFlow
from .infrastructure.storage import OutputLayout
from .platforms import resolve_platforms
from .services import (
    CaptureOrchestrator,
    DefaultPageSettler,
    RouteScreenDiscoverer,
    ViewportCapturer,
)

_SETTING_NAMES = frozenset(Settings.__dataclass_fields__)


class ExpoShotter:
    """Capture an Expo web app for multiple store platforms.

    This class is a thin facade: configuration lives in :class:`Settings`, and
    discovery, capture and reporting are separate injectable services.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 19006,
        output_dir: str | Path = "store-assets",
        *,
        scheme: str = "http",
        base_path: str = "",
        platforms: Iterable[str | PlatformSpec] | None = None,
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
        full_page: str = "never",
        full_page_fit: str = "stretch",
        progress: Any | None = None,
    ) -> None:
        resolved = resolve_platforms(platforms)
        self._settings = build_settings(
            host=host,
            port=port,
            output_dir=output_dir,
            scheme=scheme,
            base_path=base_path,
            platforms=resolved,
            devices=devices,
            variants=variants,
            recommended_only=recommended_only,
            routes=routes,
            flows=flows,
            wait_for_text=wait_for_text,
            wait_ms=wait_ms,
            max_routes=max_routes,
            max_depth=max_depth,
            exclude=exclude,
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

        self.output = OutputLayout(output_dir)
        self.platforms = tuple(resolved)
        self.settler = DefaultPageSettler(self._settings)
        self.discoverer = RouteScreenDiscoverer(self._settings)
        self.capturer = ViewportCapturer(self._settings, self.output, self.settler)
        self.orchestrator = CaptureOrchestrator(
            self._settings, self.output, self.discoverer, self.capturer
        )

    @property
    def settings(self) -> Settings:
        """The validated configuration used by the services."""
        return self._settings

    @property
    def base_url(self) -> str:
        return self._settings.base_url

    def run(self) -> dict[str, Any]:
        return self.orchestrator.run()

    def __getattr__(self, name: str) -> Any:
        # Preserve the old attribute-based access to configuration values.
        if name in _SETTING_NAMES:
            return getattr(self._settings, name)
        raise AttributeError(f"{type(self).__name__} has no attribute {name!r}")


StoreShotter = ExpoShotter
