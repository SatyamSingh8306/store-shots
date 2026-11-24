"""Image validation and store normalization."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image

from ..core.models import GlobalRules


@dataclass(frozen=True)
class Issue:
    severity: str  # "error" | "warning"
    code: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return asdict(self)


def finalize_image(
    path: Path,
    expected_width: int,
    expected_height: int,
    rules: GlobalRules,
    max_file_size_mb: float | None = None,
) -> list[Issue]:
    """Validate a screenshot, force it to 24-bit PNG, and return any issues."""
    issues: list[Issue] = []
    limit_mb = max_file_size_mb or rules.max_file_size_mb

    try:
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            had_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
            rgb = image.convert("RGB")
    except Exception as error:
        issues.append(Issue("error", "UNREADABLE", f"Cannot read image: {error}", str(path)))
        return issues

    if (width, height) != (expected_width, expected_height):
        issues.append(
            Issue(
                "error",
                "SIZE_MISMATCH",
                f"Is {width}x{height}, expected {expected_width}x{expected_height}.",
                str(path),
            )
        )

    shortest, longest = min(width, height), max(width, height)
    if shortest < rules.min_dimension_px:
        issues.append(
            Issue(
                "error",
                "MIN_DIMENSION",
                f"Shortest side {shortest}px is below the {rules.min_dimension_px}px minimum.",
                str(path),
            )
        )
    if longest > rules.max_dimension_px:
        issues.append(
            Issue(
                "error",
                "MAX_DIMENSION",
                f"Longest side {longest}px exceeds the {rules.max_dimension_px}px maximum.",
                str(path),
            )
        )
    if longest / shortest > rules.max_aspect_ratio + 0.0001:
        issues.append(
            Issue(
                "error",
                "ASPECT_RATIO",
                f"Aspect ratio {longest / shortest:.2f}:1 exceeds the {rules.max_aspect_ratio}:1 limit.",
                str(path),
            )
        )
    if had_alpha and not rules.alpha_allowed:
        issues.append(
            Issue(
                "warning",
                "ALPHA_REMOVED",
                "Alpha channel removed; PNG must be 24-bit (no transparency).",
                str(path),
            )
        )

    try:
        rgb.save(path, format="PNG", optimize=True)
    except Exception as error:
        issues.append(Issue("error", "WRITE_FAILED", f"Cannot normalize image: {error}", str(path)))
        return issues

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > limit_mb:
        issues.append(
            Issue(
                "error",
                "FILE_SIZE",
                f"{size_mb:.1f}MB exceeds the {limit_mb}MB limit.",
                str(path),
            )
        )

    return issues
