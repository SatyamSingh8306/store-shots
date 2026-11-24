"""Page settling helpers shared by the route explorer and the capture client.

A fixed delay is not enough for real Expo apps: the JS bundle has to evaluate,
fonts and images have to decode, data fetches have to finish, and loading
placeholders have to disappear.  ``settle_page`` waits for all of those (best
effort) before a screenshot is taken.
"""

from __future__ import annotations

from playwright.sync_api import Page

HIDE_SCROLLBARS_CSS = """
html, body { scrollbar-width: none !important; -ms-overflow-style: none !important; }
html::-webkit-scrollbar, body::-webkit-scrollbar, *::-webkit-scrollbar {
  display: none !important;
}
"""

_READY_JS = "() => document.readyState === 'complete'"
_APP_ROOT_READY_JS = """() => {
  for (const id of ['root', '__next', 'app']) {
    const root = document.getElementById(id);
    if (root) {
      return root.children.length > 0 || (root.innerText || '').trim().length > 0;
    }
  }
  return (document.body.innerText || '').trim().length > 0;
}"""
_IMAGES_JS = "() => Array.from(document.images).every(img => img.complete)"

_LOADING_GONE_JS = """() => {
  const visible = (element) => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return rect.width > 4 && rect.height > 4 &&
      style.visibility !== 'hidden' && style.display !== 'none' &&
      Number(style.opacity) > 0.05;
  };

  const selectors = [
    '[role="progressbar"]',
    '[aria-busy="true"]',
    '[data-testid*="loading" i]',
    '[data-testid*="spinner" i]',
    '[class*="spinner" i]',
    '[class*="loading" i]',
    '[class*="loader" i]',
  ];
  for (const selector of selectors) {
    for (const element of document.querySelectorAll(selector)) {
      if (visible(element)) return false;
    }
  }

  const loadingText = /^(loading|please wait|preparing|starting up|just a moment)[.\\u2026\\s]*$/i;
  for (const element of document.querySelectorAll('body *')) {
    if (element.children.length) continue;
    const text = (element.innerText || '').trim();
    if (text && text.length < 40 && loadingText.test(text) && visible(element)) return false;
  }
  return true;
}"""

_DOM_STABLE_JS = """({quiet, timeout}) => new Promise((resolve) => {
  let timer = null;
  let observer = null;
  let finished = false;

  const finish = () => {
    if (finished) return;
    finished = true;
    if (timer) clearTimeout(timer);
    if (observer) observer.disconnect();
    resolve(true);
  };

  const arm = () => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(finish, quiet);
  };

  try {
    observer = new MutationObserver(arm);
    observer.observe(document.documentElement, {
      subtree: true,
      childList: true,
      attributes: true,
      characterData: true,
    });
  } catch (error) {
    finish();
    return;
  }

  setTimeout(finish, timeout);
  arm();
})"""


def _attempt(action) -> None:
    """Run a best-effort wait; a timeout must never abort a capture."""
    try:
        action()
    except Exception:
        pass


def settle_page(
    page: Page,
    *,
    network_idle: bool = True,
    network_idle_timeout_ms: int = 8000,
    wait_ms: int = 0,
    wait_for_selector: str | None = None,
    navigation_timeout_ms: int = 30000,
    wait_for_loading: bool = True,
    dom_quiet_ms: int = 250,
    hide_scrollbars: bool = True,
) -> None:
    """Wait until the page is fully rendered and visually quiet.

    Every wait is best effort: a page that never reaches network idle (for
    example because of an HMR WebSocket) still gets captured after the
    timeout instead of failing the whole run.
    """
    timeout = max(1000, navigation_timeout_ms)

    _attempt(lambda: page.wait_for_function(_READY_JS, timeout=min(5000, timeout)))

    if network_idle:
        _attempt(
            lambda: page.wait_for_load_state(
                "networkidle", timeout=min(max(500, network_idle_timeout_ms), timeout)
            )
        )

    if wait_for_loading:
        _attempt(
            lambda: page.wait_for_function(_LOADING_GONE_JS, timeout=min(10000, timeout))
        )

    _attempt(lambda: page.evaluate("() => document.fonts.ready.then(() => true)"))
    _attempt(lambda: page.wait_for_function(_IMAGES_JS, timeout=min(5000, timeout)))
    _attempt(lambda: page.wait_for_function(_APP_ROOT_READY_JS, timeout=min(10000, timeout)))

    if hide_scrollbars:
        _attempt(lambda: page.add_style_tag(content=HIDE_SCROLLBARS_CSS))

    if wait_for_selector:
        _attempt(lambda: page.wait_for_selector(wait_for_selector, timeout=timeout))

    _attempt(
        lambda: page.evaluate(
            _DOM_STABLE_JS,
            {"quiet": max(0, dom_quiet_ms), "timeout": min(5000, timeout)},
        )
    )

    if wait_ms:
        page.wait_for_timeout(wait_ms)
