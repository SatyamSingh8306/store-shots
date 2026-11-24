"""Multi-store screenshots for Expo web apps."""

from .cli import print_dry_run, print_summary
from .client import ExpoShotter, StoreShotter
from .config import Settings, build_settings
from .core import (
    Capturer,
    DeviceType,
    ExtraAsset,
    GlobalRules,
    PageSettler,
    PlatformSpec,
    ProgressReporter,
    ScreenDiscoverer,
    Variant,
)
from .flows import CaptureFlow, Step, load_flows, run_steps
from .infrastructure import (
    Issue,
    OutputLayout,
    StageProgress,
    check_dimensions,
    settle_page,
)
from .platforms import (
    AMAZON,
    APP_STORE,
    PLATFORMS,
    PLAY_STORE,
    describe,
    get_platform,
    resolve_platforms,
)
from .profiles import get_device, get_variant, iter_targets
from .routes import RouteCrawler, slugify_route
from .services import (
    CaptureOrchestrator,
    DefaultPageSettler,
    RouteScreenDiscoverer,
    ViewportCapturer,
)
from .version import __version__

__all__ = [
    "AMAZON",
    "APP_STORE",
    "PLATFORMS",
    "PLAY_STORE",
    "CaptureFlow",
    "CaptureOrchestrator",
    "Capturer",
    "DefaultPageSettler",
    "DeviceType",
    "ExpoShotter",
    "ExtraAsset",
    "GlobalRules",
    "Issue",
    "OutputLayout",
    "PageSettler",
    "PlatformSpec",
    "ProgressReporter",
    "RouteCrawler",
    "RouteScreenDiscoverer",
    "ScreenDiscoverer",
    "Settings",
    "StageProgress",
    "Step",
    "StoreShotter",
    "Variant",
    "ViewportCapturer",
    "__version__",
    "build_settings",
    "check_dimensions",
    "describe",
    "get_device",
    "get_platform",
    "get_variant",
    "iter_targets",
    "load_flows",
    "print_dry_run",
    "print_summary",
    "resolve_platforms",
    "run_steps",
    "settle_page",
    "slugify_route",
]
