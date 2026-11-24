"""Wait for pages to settle before capture."""

from __future__ import annotations

from playwright.sync_api import Page

from ..config.settings import Settings
from ..infrastructure.waits import settle_page


class DefaultPageSettler:
    """Wait for a page to be ready, quiet and fully rendered."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def settle(self, page: Page, *, network_idle_timeout_ms: int = 8000) -> None:
        settings = self.settings
        settle_page(
            page,
            network_idle=settings.network_idle,
            network_idle_timeout_ms=network_idle_timeout_ms,
            wait_ms=settings.wait_ms,
            wait_for_selector=settings.wait_for_selector,
            navigation_timeout_ms=settings.navigation_timeout_ms,
            wait_for_loading=settings.wait_for_loading,
            dom_quiet_ms=settings.dom_quiet_ms,
        )
