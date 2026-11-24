"""Platform preset registry."""

from __future__ import annotations

from collections.abc import Iterable

from ..core.models import PlatformSpec
from .amazon import AMAZON
from .appstore import APP_STORE
from .playstore import PLAY_STORE

PLATFORMS: dict[str, PlatformSpec] = {
    platform.id: platform for platform in (PLAY_STORE, APP_STORE, AMAZON)
}

__all__ = [
    "AMAZON",
    "APP_STORE",
    "PLATFORMS",
    "PLAY_STORE",
    "describe",
    "get_platform",
    "resolve_platforms",
]


def get_platform(platform_id: str) -> PlatformSpec | None:
    return PLATFORMS.get(platform_id)


def resolve_platforms(
    requested: Iterable[str | PlatformSpec] | None = None,
) -> list[PlatformSpec]:
    """Resolve ids and/or custom PlatformSpec objects into a stable list."""
    if requested is None:
        return list(PLATFORMS.values())

    resolved: list[PlatformSpec] = []
    for item in requested:
        if isinstance(item, PlatformSpec):
            resolved.append(item)
            continue
        platform = PLATFORMS.get(item)
        if platform is None:
            raise ValueError(
                f"Unknown platform '{item}'. Choose from: {', '.join(sorted(PLATFORMS))} "
                "or pass a custom PlatformSpec."
            )
        resolved.append(platform)
    return resolved


def iter_targets(platform: PlatformSpec, device_ids=None, variant_ids=None, recommended_only=False):
    from ..profiles import iter_targets as _iter

    return _iter(platform, device_ids, variant_ids, recommended_only)


def describe() -> str:
    lines: list[str] = []
    for platform in PLATFORMS.values():
        lines.append(f"== {platform.id}  -  {platform.label} ==")
        for device in platform.devices:
            lines.append(f"  {device.id}  -  {device.label}")
            for variant in device.variants:
                star = "" if variant.recommended else " (optional)"
                lines.append(
                    f"      {variant.id:<10} {variant.width}x{variant.height}"
                    f"  {variant.aspect_ratio}{star}"
                )
            for asset in device.extra_assets:
                lines.append(
                    f"      {asset.id:<10} {asset.width}x{asset.height}  (asset)"
                )
        for asset in platform.extra_assets:
            lines.append(
                f"  {asset.id:<10} {asset.width}x{asset.height}  (platform asset)"
            )
        lines.append("")
    return "\n".join(lines).rstrip()
