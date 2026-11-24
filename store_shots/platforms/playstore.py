"""Google Play screenshot presets.

Source: https://support.google.com/googleplay/android-developer/answer/9866151

Current limits (checked 2026):

* Up to 8 screenshots per supported device type.
* PNG or JPEG, 24-bit PNG with no alpha, up to 8 MB each.
* Each side between 320 px and 3,840 px; phone/tablet aspect ratio <= 2.3:1.
* Phones: 2-8 screenshots, 9:16 portrait and/or 16:9 landscape.
* Tablets / Chromebooks: at least 4 screenshots.
* Foldables: 3-8 screenshots; include 1:1 inner, 4:3 wide inner and 10:16
  folded outer aspect ratios.
* Wear OS: at least one 1:1 screenshot, minimum 384x384.
* Android TV: at least one screenshot plus a 1280x720 banner.
* Automotive: at least 2 portrait (800x1280) and 2 landscape (1024x768).
* Android XR: 4-8 screenshots, 8:5 aspect ratio, recommended 3840x2400
  (minimum 1920x1200), up to 8 MB each.
"""

from ..core.models import DeviceType, ExtraAsset, GlobalRules, PlatformSpec, Variant

PLAY_STORE = PlatformSpec(
    id="playstore",
    label="Google Play",
    output_folder="google-play",
    source="https://support.google.com/googleplay/android-developer/answer/9866151",
    rules=GlobalRules(
        min_dimension_px=320,
        max_dimension_px=3840,
        max_aspect_ratio=2.3,
        max_file_size_mb=8.0,
        minimum_screenshots_total=2,
    ),
    extra_assets=(
        ExtraAsset("feature-graphic", "Feature graphic", 1024, 500, required=True),
    ),
    devices=(
        DeviceType(
            id="phone",
            label="Phone",
            min_screenshots=2,
            max_screenshots=8,
            variants=(
                Variant("portrait", "Portrait", "portrait", "9:16", 1080, 1920),
                Variant("landscape", "Landscape", "landscape", "16:9", 1920, 1080),
                Variant("square", "Square", "square", "1:1", 1080, 1080, recommended=False),
            ),
        ),
        DeviceType(
            id="foldable",
            label="Foldable",
            css_dpr=2,
            min_screenshots=3,
            max_screenshots=8,
            variants=(
                Variant("square", "Unfolded square (1:1)", "square", "1:1", 1920, 1920),
                Variant("wide", "Unfolded wide (4:3)", "landscape", "4:3", 2560, 1920),
                Variant("outer", "Folded outer (10:16)", "portrait", "10:16", 1080, 1728),
                Variant(
                    "outer-landscape",
                    "Folded outer (16:10)",
                    "landscape",
                    "16:10",
                    1728,
                    1080,
                    recommended=False,
                ),
            ),
        ),
        DeviceType(
            id="tablet-7",
            label="7-inch tablet",
            min_screenshots=4,
            max_screenshots=8,
            variants=(
                Variant("portrait", "Portrait", "portrait", "5:8", 1200, 1920),
                Variant("landscape", "Landscape", "landscape", "8:5", 1920, 1200),
            ),
        ),
        DeviceType(
            id="tablet-10",
            label="10-inch tablet",
            css_dpr=2,
            min_screenshots=4,
            max_screenshots=8,
            variants=(
                Variant("portrait", "Portrait", "portrait", "5:8", 1600, 2560),
                Variant("landscape", "Landscape", "landscape", "8:5", 2560, 1600),
            ),
        ),
        DeviceType(
            id="chromebook",
            label="Chromebook",
            css_dpr=2,
            mobile_emulation=False,
            min_screenshots=4,
            max_screenshots=8,
            variants=(
                Variant("landscape", "Landscape", "landscape", "16:9", 1920, 1080),
                Variant("portrait", "Portrait", "portrait", "9:16", 1080, 1920),
            ),
        ),
        DeviceType(
            id="desktop",
            label="Desktop / laptop",
            css_dpr=1,
            mobile_emulation=False,
            min_screenshots=4,
            max_screenshots=8,
            variants=(
                Variant("landscape", "Landscape", "landscape", "16:9", 1920, 1080),
                Variant(
                    "wide",
                    "Wide (1440p)",
                    "landscape",
                    "16:9",
                    2560,
                    1440,
                    recommended=False,
                ),
            ),
        ),
        DeviceType(
            id="android-tv",
            label="Android TV",
            css_dpr=1,
            mobile_emulation=False,
            min_screenshots=1,
            max_screenshots=8,
            extra_assets=(ExtraAsset("banner", "TV banner", 1280, 720, required=True),),
            variants=(Variant("landscape", "Landscape", "landscape", "16:9", 1920, 1080),),
        ),
        DeviceType(
            id="wear-os",
            label="Wear OS",
            css_dpr=2,
            min_screenshots=1,
            max_screenshots=8,
            variants=(Variant("square", "Square", "square", "1:1", 480, 480),),
        ),
        DeviceType(
            id="automotive",
            label="Android Automotive OS",
            css_dpr=1,
            mobile_emulation=False,
            min_screenshots=2,
            max_screenshots=8,
            variants=(
                Variant("portrait", "Portrait", "portrait", "5:8", 800, 1280),
                Variant("landscape", "Landscape", "landscape", "4:3", 1024, 768),
            ),
        ),
        DeviceType(
            id="android-xr",
            label="Android XR",
            css_dpr=2,
            mobile_emulation=False,
            min_screenshots=4,
            max_screenshots=8,
            max_file_size_mb=8.0,
            variants=(Variant("wide", "Wide", "landscape", "8:5", 3840, 2400),),
        ),
    ),
)
