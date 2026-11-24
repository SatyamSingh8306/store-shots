"""Scripted interaction flows used before taking a screenshot.

A flow drives the app to a specific screen (complete onboarding, open a tab,
etc.) and waits for concrete content, so captures never show loading states.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.sync_api import Page

_FILL_JS = """([placeholder, value]) => {
  const input = [...document.querySelectorAll('input')].find(
    i => i.placeholder === placeholder
  );
  if (!input) return false;
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value'
  ).set;
  setter.call(input, value);
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return true;
}"""

_CLICK_TEXT_JS = """([needle, exact]) => {
  const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
  const matches = (value) => {
    const candidate = normalize(value);
    if (!candidate) return false;
    return exact ? candidate === needle : candidate.includes(needle);
  };
  const isVisible = (element) => {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return rect.width > 1 && rect.height > 1 &&
      style.visibility !== 'hidden' && style.display !== 'none' &&
      Number(style.opacity) > 0.05;
  };

  const clickable = [
    'button',
    'a',
    'input[type="button"]',
    'input[type="submit"]',
    '[role="button"]',
    '[role="tab"]',
    '[role="link"]',
    '[role="menuitem"]',
    '[tabindex]',
  ].join(', ');

  // Pressable/TouchableOpacity in React Native Web can be plain divs with a
  // pointer cursor, so use those as a fallback when matching text.
  const fallback = [];
  for (const element of document.querySelectorAll('div, span, li')) {
    if (!isVisible(element)) continue;
    const style = getComputedStyle(element);
    if (style.cursor === 'pointer' || element.tabIndex >= 0) fallback.push(element);
  }

  const candidates = [];
  const clickables = new Set([...document.querySelectorAll(clickable), ...fallback]);
  for (const element of clickables) {
    if (!isVisible(element)) continue;
    if (element.disabled || element.getAttribute('aria-disabled') === 'true') continue;
    const label = element.getAttribute('aria-label') ||
      element.getAttribute('title') ||
      element.getAttribute('alt') ||
      element.innerText ||
      element.textContent ||
      element.value ||
      '';
    if (!matches(label)) continue;
    // Prefer the most specific matching element (fewest descendants).
    candidates.push([element.querySelectorAll('*').length, element]);
  }

  if (!candidates.length) return false;
  candidates.sort((left, right) => left[0] - right[0]);
  const target = candidates[0][1];
  try {
    target.scrollIntoView({block: 'center', inline: 'center'});
  } catch (error) {
    // Non-visual element; clicking it is still the best we can do.
  }
  target.click();
  return true;
}"""


@dataclass(frozen=True)
class Step:
    """One action in a capture flow."""

    action: str
    value: str | None = None
    value2: str | None = None
    exact: bool = False
    timeout_ms: int = 30000

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Step:
        return cls(
            action=str(data["action"]),
            value=data.get("value"),
            value2=data.get("value2"),
            exact=bool(data.get("exact", False)),
            timeout_ms=int(data.get("timeout_ms", 30000)),
        )


@dataclass(frozen=True)
class CaptureFlow:
    """A screen to capture, reached by running `steps` first."""

    id: str
    label: str | None = None
    route: str = "/"
    steps: tuple[Step, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CaptureFlow:
        return cls(
            id=str(data["id"]),
            label=data.get("label"),
            route=str(data.get("route", "/")),
            steps=tuple(Step.from_dict(item) for item in data.get("steps", [])),
        )


def load_flows(path: str | Path) -> list[CaptureFlow]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    items = payload.get("flows", payload) if isinstance(payload, dict) else payload
    return [CaptureFlow.from_dict(item) for item in items]


def _retry_until(page: Page, expression: str, argument: list[Any], timeout_ms: int) -> bool:
    """Keep trying an action until its target exists or the timeout expires."""
    deadline = time.monotonic() + max(0, timeout_ms) / 1000
    while True:
        if page.evaluate(expression, argument):
            return True
        if time.monotonic() >= deadline:
            return False
        page.wait_for_timeout(200)


def run_steps(page: Page, steps: Iterable[Step]) -> list[str]:
    """Execute steps in order; return a log of what happened."""
    log: list[str] = []
    for step in steps:
        action = step.action
        value = step.value or ""

        if action == "fill":
            ok = _retry_until(page, _FILL_JS, [value, step.value2 or ""], step.timeout_ms)
            log.append(f"fill {value}: {'ok' if ok else 'not found'}")
        elif action == "click_text":
            ok = _retry_until(page, _CLICK_TEXT_JS, [value, step.exact], step.timeout_ms)
            log.append(f"click_text {value}: {'ok' if ok else 'not found'}")
        elif action == "click_selector":
            page.click(value, timeout=step.timeout_ms)
            log.append(f"click_selector {value}")
        elif action == "wait_for_text":
            page.wait_for_function(
                "needle => (document.body.innerText || '').includes(needle)",
                arg=value,
                timeout=step.timeout_ms,
            )
            log.append(f"wait_for_text {value}")
        elif action == "wait_text_gone":
            page.wait_for_function(
                "needle => !(document.body.innerText || '').includes(needle)",
                arg=value,
                timeout=step.timeout_ms,
            )
            log.append(f"wait_text_gone {value}")
        elif action == "wait_for_selector":
            page.wait_for_selector(value, state="visible", timeout=step.timeout_ms)
            log.append(f"wait_for_selector {value}")
        elif action == "wait_ms":
            page.wait_for_timeout(int(value or 0))
            log.append(f"wait_ms {value}")
        elif action == "scroll":
            page.mouse.wheel(0, int(value or 0))
            page.wait_for_timeout(200)
            log.append(f"scroll {value}")
        elif action == "press":
            page.keyboard.press(value)
            log.append(f"press {value}")
        else:
            raise ValueError(f"Unknown flow action: {action}")
    return log
