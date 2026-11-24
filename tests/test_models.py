from store_shots.core.models import DeviceType, GlobalRules, PlatformSpec, Variant


def test_variant_size() -> None:
    variant = Variant("portrait", "Portrait", "portrait", "9:16", 1080, 1920)
    assert variant.size == (1080, 1920)


def test_platform_folder_fallback() -> None:
    platform = PlatformSpec(id="custom", label="Custom", devices=())
    assert platform.folder == "custom"

    named = PlatformSpec(id="custom", label="Custom", devices=(), output_folder="my-store")
    assert named.folder == "my-store"


def test_device_defaults() -> None:
    device = DeviceType(id="d", label="D", variants=())
    assert device.css_dpr == 2
    assert device.mobile_emulation is True
    assert device.max_screenshots == 10


def test_global_rules_defaults() -> None:
    rules = GlobalRules()
    assert rules.min_dimension_px == 320
    assert rules.max_dimension_px == 4096
    assert rules.alpha_allowed is False
