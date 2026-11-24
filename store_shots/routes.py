"""Automatic screen discovery for Expo Router web apps.

The explorer does two things:

* follows internal ``<a href>`` links (Expo Router renders these for ``<Link>``)
* clicks visible buttons, tabs and ``role=button`` elements, replaying the click
  path from the app root to reach screens that live behind interaction (tabs,
  onboarding, modals, ...)

Each discovered screen is returned as a :class:`~store_shots.flows.CaptureFlow`
so the capture client can replay it later before taking a screenshot.
"""

from __future__ import annotations

import re
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .flows import CaptureFlow, Step, run_steps
from .infrastructure.waits import settle_page

_IGNORED_PREFIXES = (
    "/_expo",
    "/assets",
    "/static",
    "/node_modules",
    "/@fs",
    "/@id",
    "/favicon",
)

_ASSET_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".css", ".js", ".mjs", ".map", ".json", ".woff", ".woff2",
    ".ttf", ".otf", ".mp4", ".pdf", ".zip",
}

_SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "#")

# Actions that are destructive or leave the app; clicking them while exploring
# would either break the session or capture an error page.
_DESTRUCTIVE_RE = re.compile(
    r"\b("
    r"log ?out|sign ?out|delete|remove|cancel|close|dismiss|exit|quit|"
    r"reset|clear|purchase|buy|subscribe|uninstall|go back|back"
    r")\b",
    re.IGNORECASE,
)

_READ_ACTIONS_JS = """() => {
  const selectors = [
    'a[href]',
    'button',
    'input[type="button"]',
    'input[type="submit"]',
    '[role="button"]',
    '[role="tab"]',
    '[role="link"]',
    '[role="menuitem"]',
  ].join(', ');

  const isVisible = (element) => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return rect.width > 4 && rect.height > 4 &&
      style.visibility !== 'hidden' && style.display !== 'none' &&
      Number(style.opacity) > 0.05;
  };

  const labelOf = (element) => (
    element.getAttribute('aria-label') ||
    element.getAttribute('title') ||
    element.getAttribute('alt') ||
    element.innerText ||
    element.textContent ||
    element.value ||
    ''
  ).replace(/\\s+/g, ' ').trim();

  // React Native Web's Pressable/TouchableOpacity often render as plain divs
  // with a pointer cursor (no role attribute), so include those as well.
  const extra = [];
  for (const element of document.querySelectorAll('div, span, li, [tabindex]')) {
    if (!isVisible(element)) continue;
    if (element.disabled || element.getAttribute('aria-disabled') === 'true') continue;
    const style = getComputedStyle(element);
    const tabbable = element.tabIndex >= 0;
    if (style.cursor !== 'pointer' && !tabbable) continue;
    const text = labelOf(element);
    if (!text || text.length > 80) continue;
    extra.push(element);
  }

  const actions = [];
  const seen = new Set();
  const candidates = new Set([...document.querySelectorAll(selectors), ...extra]);
  for (const element of candidates) {
    if (!isVisible(element)) continue;
    if (element.disabled || element.getAttribute('aria-disabled') === 'true') continue;

    const text = labelOf(element).slice(0, 160);
    const href = element.getAttribute('href');
    const key = `${element.tagName}|${href || ''}|${text}`;
    if (seen.has(key)) continue;
    seen.add(key);

    let selector = null;
    if (element.id) {
      selector = '#' + CSS.escape(element.id);
    } else if (element.getAttribute('data-testid')) {
      selector = `[data-testid="${CSS.escape(element.getAttribute('data-testid'))}"]`;
    }

    actions.push({text, href, selector});
  }
  return actions;
}"""

_STATE_SIGNATURE_JS = """() => {
  const headings = [...document.querySelectorAll('h1, h2, h3, h4, [role="heading"]')]
    .map((element) => (element.innerText || '').trim())
    .filter(Boolean)
    .join(' | ');
  const text = headings || (document.body.innerText || '');
  const controls = document.querySelectorAll(
    'button, a, [role="button"], [role="tab"], [role="link"]'
  ).length;
  const normalized = text
    .replace(/\\s+/g, ' ')
    .replace(/\\d+/g, '#')
    .trim()
    .slice(0, 240);
  return `${controls}|${normalized}`;
}"""


def slugify_route(route: str) -> str:
    """Turn '/profile/settings?tab=1' into 'profile-settings-tab-1'."""
    parsed = urlparse(route)
    raw = f"{parsed.path}{'-' + parsed.query if parsed.query else ''}"
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-").lower()
    return slug or "home"


class RouteCrawler:
    """Breadth-first explorer for internal links *and* interactive controls."""

    def __init__(
        self,
        page: Page,
        base_url: str,
        *,
        max_routes: int = 25,
        max_depth: int = 3,
        exclude: tuple[str, ...] | list[str] = (),
        wait_ms: int = 500,
        navigation_timeout_ms: int = 20000,
        wait_for_selector: str | None = None,
        click_buttons: bool = True,
        max_actions_per_screen: int = 24,
        network_idle: bool = True,
        wait_for_loading: bool = True,
        dom_quiet_ms: int = 250,
    ) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.base_origin = urlparse(base_url)
        self.max_routes = max(1, max_routes)
        self.max_depth = max(0, max_depth)
        self.exclude = tuple(exclude)
        self.wait_ms = max(0, wait_ms)
        self.navigation_timeout_ms = navigation_timeout_ms
        self.wait_for_selector = wait_for_selector
        self.click_buttons = click_buttons
        self.max_actions_per_screen = max(1, max_actions_per_screen)
        self.network_idle = network_idle
        self.wait_for_loading = wait_for_loading
        self.dom_quiet_ms = max(0, dom_quiet_ms)

    # ------------------------------------------------------------------ public
    def discover(self) -> list[str]:
        """Return route paths only (links are followed, buttons are not)."""
        root = urlparse(self.base_url).path or "/"
        queue: deque[tuple[str, int]] = deque([(root, 0)])
        seen: set[str] = set()
        routes: list[str] = []

        while queue and len(routes) < self.max_routes:
            route, depth = queue.popleft()
            if route in seen:
                continue
            seen.add(route)
            routes.append(route)

            if depth >= self.max_depth:
                continue

            for link in self._read_links(route):
                if link in seen or self._excluded(link):
                    continue
                queue.append((link, depth + 1))

        return routes

    def discover_screens(self) -> list[CaptureFlow]:
        """Return every reachable screen, including ones behind button clicks."""
        root = urlparse(self.base_url).path or "/"
        queue: deque[tuple[str, tuple[Step, ...]]] = deque([(root, ())])
        queued: set[tuple[str, tuple[Step, ...]]] = {(root, ())}
        seen_routes: set[str] = {root}
        seen_states: set[str] = set()
        used_ids: set[str] = set()
        screens: list[CaptureFlow] = []
        max_attempts = max(30, self.max_routes * 10)
        attempts = 0

        while queue and len(screens) < self.max_routes and attempts < max_attempts:
            route, steps = queue.popleft()
            attempts += 1
            if len(steps) > self.max_depth:
                continue
            if not self._restore(route, steps):
                continue

            state = self._state_key(route)
            if state in seen_states:
                continue
            seen_states.add(state)
            screens.append(self._make_flow(route, steps, used_ids))

            if len(steps) >= self.max_depth:
                continue

            actions = self._read_actions()
            # Inspect buttons/tabs before plain links so the action budget is
            # spent on interactive controls first.
            actions.sort(
                key=lambda item: (bool(item.get("href")), (item.get("text") or "").lower())
            )
            for action in actions[: self.max_actions_per_screen]:
                href = action.get("href")
                if href:
                    target = self._normalize(href)
                    if target and target not in seen_routes:
                        key = (target, ())
                        if key not in queued and len(queue) < max_attempts:
                            seen_routes.add(target)
                            queued.add(key)
                            queue.append(key)
                    continue

                if not self.click_buttons:
                    continue

                text = action.get("text") or ""
                selector = action.get("selector")
                if not text and not selector:
                    continue
                if self._skip_action(text):
                    continue

                if text:
                    step = Step("click_text", text, exact=True)
                else:
                    step = Step("click_selector", selector)
                if step in steps:
                    continue

                key = (route, steps + (step,))
                if key in queued or len(queue) >= max_attempts:
                    continue
                queued.add(key)
                queue.append(key)

        return screens

    # ----------------------------------------------------------------- helpers
    def _excluded(self, route: str) -> bool:
        if any(route.startswith(prefix) for prefix in _IGNORED_PREFIXES):
            return True
        if Path(route).suffix.lower() in _ASSET_SUFFIXES:
            return True
        return any(pattern in route for pattern in self.exclude)

    def _normalize(self, href: str) -> str | None:
        if not href:
            return None
        href = href.strip()
        if href.startswith(_SKIP_SCHEMES):
            return None

        absolute = urljoin(f"{self.base_url}/", href)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            return None
        if parsed.netloc != self.base_origin.netloc:
            return None

        path = parsed.path or "/"
        route = path + (f"?{parsed.query}" if parsed.query else "")
        if self._excluded(route):
            return None
        return route

    def _skip_action(self, text: str) -> bool:
        if not text:
            return False
        return bool(_DESTRUCTIVE_RE.search(text))

    def _settle(self) -> None:
        settle_page(
            self.page,
            network_idle=self.network_idle,
            network_idle_timeout_ms=2500,
            wait_ms=self.wait_ms,
            wait_for_selector=self.wait_for_selector,
            navigation_timeout_ms=min(self.navigation_timeout_ms, 10000),
            wait_for_loading=self.wait_for_loading,
            dom_quiet_ms=self.dom_quiet_ms,
        )

    def _restore(self, route: str, steps: tuple[Step, ...]) -> bool:
        url = urljoin(f"{self.base_url}/", route.lstrip("/"))
        try:
            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.navigation_timeout_ms,
            )
        except PlaywrightTimeoutError:
            return False
        except Exception:
            return False

        self._settle()
        if steps:
            try:
                run_steps(self.page, steps)
            except Exception:
                return False
            self._settle()
        return True

    def _state_key(self, fallback: str) -> str:
        try:
            current = urlparse(self.page.url)
            path = current.path + (f"?{current.query}" if current.query else "")
            signature = self.page.evaluate(_STATE_SIGNATURE_JS)
            return f"{path}|{signature}"
        except Exception:
            return fallback

    def _make_flow(
        self, route: str, steps: tuple[Step, ...], used_ids: set[str]
    ) -> CaptureFlow:
        base = slugify_route(route)
        label = None
        if steps:
            last = steps[-1]
            label = last.value or last.action
            base = f"{base}-{slugify_route(str(label))}"

        candidate = base or "screen"
        suffix = 2
        while candidate in used_ids:
            candidate = f"{base}-{suffix}"
            suffix += 1
        used_ids.add(candidate)
        return CaptureFlow(id=candidate, label=label, route=route, steps=steps)

    def _read_actions(self) -> list[dict[str, str | None]]:
        try:
            actions = self.page.evaluate(_READ_ACTIONS_JS)
        except Exception:
            return []

        result: list[dict[str, str | None]] = []
        for action in actions or []:
            text = (action.get("text") or "").strip()
            href = action.get("href")
            selector = action.get("selector")
            result.append({"text": text, "href": href, "selector": selector})
        return result

    def _read_links(self, route: str) -> list[str]:
        url = urljoin(f"{self.base_url}/", route.lstrip("/"))
        try:
            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.navigation_timeout_ms,
            )
            self._settle()
            hrefs = self.page.eval_on_selector_all(
                "a[href]", "elements => elements.map(element => element.getAttribute('href'))"
            )
        except PlaywrightTimeoutError:
            return []
        except Exception:
            return []

        links: list[str] = []
        for href in hrefs:
            normalized = self._normalize(href or "")
            if normalized and normalized not in links:
                links.append(normalized)
        return links
