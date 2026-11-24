"""Amazon Appstore screenshot presets (commonly accepted sizes).

Verify against Appstore Developer Portal before submitting; sizes can change.
"""

from ..core.models import DeviceType, GlobalRules, PlatformSpec, Variant

AMAZON = PlatformSpec(
    id="amazon",
    label="Amazon Appstore",
    output_folder="amazon-appstore",
    rules=GlobalRules(
        min_dimension_px=320,
        max_dimension_px=3840,
        max_aspect_ratio=2.0,
        max_file_size_mb=15.0,
        minimum_screenshots_total=1,
    ),
    devices=(
        DeviceType(
            id="phone",
            label="Phone",
            min_screenshots=1,
            variants=(
                Variant("portrait", "Portrait", "portrait", "9:16", 1080, 1920),
                Variant("landscape", "Landscape", "landscape", "16:9", 1920, 1080, recommended=False),
            ),
        ),
        DeviceType(
            id="tablet",
            label="Fire tablet",
            css_dpr=2,
            min_screenshots=1,
            variants=(
                Variant("landscape", "Landscape", "landscape", "16:10", 1280, 800),
                Variant("portrait", "Portrait", "portrait", "10:16", 800, 1280, recommended=False),
            ),
        ),
        DeviceType(
            id="fire-tv",
            label="Fire TV",
            css_dpr=2,
            mobile_emulation=False,
            min_screenshots=1,
            variants=(Variant("landscape", "Landscape", "landscape", "16:9", 1920, 1080),),
        ),
    ),
)
