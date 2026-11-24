"""Domain models and the interfaces between layers."""

from .models import DeviceType, ExtraAsset, GlobalRules, PlatformSpec, Variant
from .protocols import Capturer, PageSettler, ProgressReporter, ScreenDiscoverer

__all__ = [
    "Capturer",
    "DeviceType",
    "ExtraAsset",
    "GlobalRules",
    "PageSettler",
    "PlatformSpec",
    "ProgressReporter",
    "ScreenDiscoverer",
    "Variant",
]
