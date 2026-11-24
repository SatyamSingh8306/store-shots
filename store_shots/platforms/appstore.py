"""Apple App Store screenshot presets.

https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/
"""

from ..core.models import DeviceType, GlobalRules, PlatformSpec, Variant

APP_STORE = PlatformSpec(
    id="appstore",
    label="Apple App Store",
    output_folder="app-store",
    source="https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/",
    rules=GlobalRules(
        formats=("png", "jpeg", "jpg"),
        alpha_allowed=False,
        min_dimension_px=320,
        max_dimension_px=4096,
        # iPhone screenshots are taller than 2:1, so no 2:1 cap here.
        max_aspect_ratio=2.3,
        max_file_size_mb=15.0,
        minimum_screenshots_total=1,
    ),
    devices=(
        DeviceType(
            id="iphone-63",
            label="iPhone 6.3-inch (required)",
            min_screenshots=1,
            variants=(
                Variant("portrait", "Portrait", "portrait", "1206:2622", 1206, 2622),
                Variant("landscape", "Landscape", "landscape", "2622:1206", 2622, 1206, recommended=False),
            ),
        ),
        DeviceType(
            id="iphone-69",
            label="iPhone 6.9-inch",
            min_screenshots=1,
            variants=(
                Variant("portrait", "Portrait", "portrait", "1320:2868", 1320, 2868),
                Variant("landscape", "Landscape", "landscape", "2868:1320", 2868, 1320, recommended=False),
            ),
        ),
        DeviceType(
            id="ipad-13",
            label="iPad 13-inch",
            css_dpr=2,
            min_screenshots=1,
            variants=(
                Variant("portrait", "Portrait", "portrait", "2064:2752", 2064, 2752),
                Variant("landscape", "Landscape", "landscape", "2752:2064", 2752, 2064, recommended=False),
            ),
        ),
        DeviceType(
            id="apple-watch",
            label="Apple Watch Ultra",
            css_dpr=2,
            min_screenshots=1,
            variants=(Variant("square", "Display", "square", "422:514", 422, 514, recommended=False),),
        ),
    ),
)
