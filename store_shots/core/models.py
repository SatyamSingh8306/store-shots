"""Shared data models for store screenshot profiles."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GlobalRules:
    """Validation rules for a store platform."""

    formats: tuple[str, ...] = ("png", "jpeg")
    alpha_allowed: bool = False
    min_dimension_px: int = 320
    max_dimension_px: int = 4096
    max_aspect_ratio: float = 2.0
    max_file_size_mb: float = 15.0
    minimum_screenshots_total: int = 1


@dataclass(frozen=True)
class Variant:
    """One screenshot size for a device class."""

    id: str
    label: str
    orientation: str
    aspect_ratio: str
    width: int
    height: int
    recommended: bool = True

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)


@dataclass(frozen=True)
class ExtraAsset:
    """An additional required image such as the Android TV banner."""

    id: str
    label: str
    width: int
    height: int
    required: bool = False


@dataclass(frozen=True)
class DeviceType:
    """A device class inside a store platform."""

    id: str
    label: str
    variants: tuple[Variant, ...]
    min_screenshots: int = 1
    max_screenshots: int = 10
    extra_assets: tuple[ExtraAsset, ...] = ()
    max_file_size_mb: float | None = None
    # Chrome responsive emulation: CSS viewport = target_px / css_dpr.
    # DPR 2 fits a full phone/tablet screen with readable text. Large-screen
    # profiles use DPR 1 so the app renders its real desktop/large-screen
    # layout. DPR 3 renders more zoomed-in and cuts off long screens.
    css_dpr: int = 2
    mobile_emulation: bool = True


@dataclass(frozen=True)
class PlatformSpec:
    """A store platform preset (Google Play, App Store, or custom)."""

    id: str
    label: str
    devices: tuple[DeviceType, ...]
    rules: GlobalRules = field(default_factory=GlobalRules)
    output_folder: str | None = None
    source: str = ""
    notes: tuple[str, ...] = ()
    # Required store assets that are not device screenshots (e.g. the Google
    # Play feature graphic). Captured once per platform at the asset size.
    extra_assets: tuple[ExtraAsset, ...] = ()

    @property
    def folder(self) -> str:
        return self.output_folder or self.id
