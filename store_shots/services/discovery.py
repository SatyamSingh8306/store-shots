"""Discover screens from routes, flows, links and interactive controls."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from playwright.sync_api import Browser

from ..config.settings import Settings
from ..flows import CaptureFlow, Step
from ..routes import RouteCrawler, slugify_route


class RouteScreenDiscoverer:
    """Find screens via explicit routes/flows, link crawling, or button clicks."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def discover(self, browser: Browser) -> list[CaptureFlow]:
        settings = self.settings
        wait_step = (
            (Step("wait_for_text", settings.wait_for_text),) if settings.wait_for_text else ()
        )

        if settings.flows is not None:
            return list(settings.flows)
        if settings.routes is not None:
            routes = settings.routes or ("/",)
            return [
                CaptureFlow(id=slugify_route(route), route=route, steps=wait_step)
                for route in routes
            ]
        if settings.click_buttons:
            flows = self._explore_screens(browser)
            return [
                replace(flow, steps=flow.steps + wait_step) if wait_step else flow
                for flow in flows
            ]

        routes = self._crawl_routes(browser)
        return [
            CaptureFlow(id=slugify_route(route), route=route, steps=wait_step) for route in routes
        ]

    def _new_crawler(self, browser: Browser, *, click_buttons: bool) -> RouteCrawler:
        settings = self.settings
        context = browser.new_context(
            viewport={"width": 1280, "height": 720}, ignore_https_errors=True
        )
        return RouteCrawler(
            context.new_page(),
            settings.base_url,
            max_routes=settings.max_routes,
            max_depth=settings.max_depth,
            exclude=settings.exclude,
            wait_ms=settings.wait_ms,
            navigation_timeout_ms=settings.navigation_timeout_ms,
            wait_for_selector=settings.wait_for_selector,
            click_buttons=click_buttons,
            max_actions_per_screen=settings.max_actions_per_screen,
            network_idle=settings.network_idle,
            wait_for_loading=settings.wait_for_loading,
            dom_quiet_ms=settings.dom_quiet_ms,
        )

    def _explore_screens(self, browser: Browser) -> list[CaptureFlow]:
        crawler = self._new_crawler(browser, click_buttons=True)
        try:
            return crawler.discover_screens() or [CaptureFlow(id="home", route="/")]
        finally:
            crawler.page.context.close()

    def _crawl_routes(self, browser: Browser) -> list[str]:
        crawler = self._new_crawler(browser, click_buttons=False)
        try:
            return crawler.discover() or ["/"]
        finally:
            crawler.page.context.close()




def flow_to_shot(flow: CaptureFlow) -> dict[str, Any]:
    """Convert a discovered flow into the serializable shot dictionary."""
    return {
        "id": flow.id,
        "label": flow.label or flow.id,
        "route": flow.route,
        "steps": [step.__dict__ for step in flow.steps],
    }
