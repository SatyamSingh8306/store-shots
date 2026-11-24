"""Helpers for working with device/variant profiles of any platform."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .core.models import DeviceType, PlatformSpec, Variant


def get_device(platform: PlatformSpec, device_id: str) -> DeviceType | None:
    return next((device for device in platform.devices if device.id == device_id), None)


def get_variant(platform: PlatformSpec, device_id: str, variant_id: str) -> Variant | None:
    device = get_device(platform, device_id)
    if device is None:
        return None
    return next((variant for variant in device.variants if variant.id == variant_id), None)


def iter_targets(
    platform: PlatformSpec,
    device_ids: Iterable[str] | None = None,
    variant_ids: Iterable[str] | None = None,
    recommended_only: bool = False,
) -> Iterator[tuple[DeviceType, Variant]]:
    """Yield (device, variant) pairs for a platform in a stable order."""
    device_filter = set(device_ids) if device_ids else None
    variant_filter = set(variant_ids) if variant_ids else None

    for device in platform.devices:
        if device_filter is not None and device.id not in device_filter:
            continue
        for variant in device.variants:
            if recommended_only and not variant.recommended:
                continue
            if variant_filter is not None and variant.id not in variant_filter:
                continue
            yield device, variant
