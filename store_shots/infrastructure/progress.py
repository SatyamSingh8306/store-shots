"""ASCII stage progress for the CLI (no emojis, no colors).

Uses `alive-progress` when stdout is a terminal, and falls back to a small
built-in spinner otherwise.  Redirected output always gets one plain ``[..]``
line per stage so logs stay readable.  ``tick()`` advances the bar once per
captured image.
"""

from __future__ import annotations

import sys
import threading
import time
from typing import Any, TextIO

from alive_progress import alive_bar as _alive_bar


class StageProgress:
    """Show the current stage while work runs."""

    FRAMES = ("|", "/", "-", "\\")

    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream if stream is not None else sys.stdout
        self.interactive = bool(getattr(self.stream, "isatty", lambda: False)())
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._text = "starting"
        self._frame = 0
        self._started = time.monotonic()
        self._thread: threading.Thread | None = None
        self._alive_ctx: Any | None = None
        self._alive_bar: Any | None = None

        if not self.interactive:
            return

        if _alive_bar is not None:
            try:
                self._alive_ctx = _alive_bar(
                    title="store-shots",
                    theme="classic",  # ASCII spinner/bar, no emojis
                    length=30,
                    file=self.stream,
                    receipt=True,
                    enrich_print=False,
                )
                self._alive_bar = self._alive_ctx.__enter__()
                self._alive_bar.text(self._text)
                return
            except Exception:
                self._alive_ctx = None
                self._alive_bar = None

        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def _render(self, frame: str) -> None:
        with self._lock:
            self.stream.write(f"\r[{frame}] {self._text}")
            self.stream.flush()

    def _animate(self) -> None:
        while not self._stop.wait(0.1):
            self._frame = (self._frame + 1) % len(self.FRAMES)
            self._render(self.FRAMES[self._frame])

    def update(self, text: str) -> None:
        """Set the current stage text."""
        self._text = text
        if self._alive_bar is not None:
            self._alive_bar.text(text)
            return
        if self.interactive:
            self._render(self.FRAMES[self._frame])
        else:
            with self._lock:
                self.stream.write(f"[..] {text}\n")
                self.stream.flush()

    def tick(self, count: int = 1) -> None:
        """Advance the bar by one (or more) completed captures."""
        if self._alive_bar is not None:
            self._alive_bar(count)
        elif self.interactive:
            self._frame = (self._frame + 1) % len(self.FRAMES)
            self._render(self.FRAMES[self._frame])

    def finish(self, text: str | None = None) -> None:
        """Stop animating; alive-progress prints its own final receipt."""
        if text:
            self._text = text
        if self._alive_ctx is not None:
            self._close_alive(None, None, None)
            return

        elapsed = time.monotonic() - self._started
        self._halt()
        with self._lock:
            if self.interactive:
                self.stream.write("\r" + " " * 72 + "\r")
            self.stream.write(f"[done] {self._text} in {elapsed:.1f}s\n")
            self.stream.flush()

    def fail(self, message: str) -> None:
        """Stop animating and report a failure."""
        if self._alive_ctx is not None:
            self._close_alive(Exception, Exception(message), None)
            with self._lock:
                self.stream.write(f"[fail] {message}\n")
                self.stream.flush()
            return

        self._halt()
        with self._lock:
            if self.interactive:
                self.stream.write("\r" + " " * 72 + "\r")
            self.stream.write(f"[fail] {message}\n")
            self.stream.flush()

    def _close_alive(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        context, self._alive_ctx = self._alive_ctx, None
        self._alive_bar = None
        if context is not None:
            context.__exit__(exc_type, exc, traceback)

    def _halt(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
            self._thread = None
