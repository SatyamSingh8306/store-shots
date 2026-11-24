import pytest

from store_shots.core.models import DeviceType, Variant
from store_shots.settings import Settings, build_settings


def device() -> DeviceType:
    return DeviceType(
        id="phone",
        label="Phone",
        variants=(Variant("portrait", "Portrait", "portrait", "9:16", 1080, 1920),),
        min_screenshots=2,
        max_screenshots=8,
    )


def test_base_url() -> None:
    settings = Settings(host="example.com", port=19006, scheme="https", base_path="/app/")
    assert settings.base_url == "https://example.com:19006/app"


def test_exact_screen_count_overrides_profile_limits() -> None:
    settings = Settings(screens=3)
    assert settings.min_for(device()) == 3
    assert settings.max_for(device()) == 3


def test_profile_limits_are_used_without_overrides() -> None:
    settings = Settings()
    assert settings.min_for(device()) == 2
    assert settings.max_for(device()) == 8


@pytest.mark.parametrize("value", [0, -1])
def test_invalid_counts_are_rejected(value: int) -> None:
    with pytest.raises(ValueError):
        Settings(screens=value)
    with pytest.raises(ValueError):
        Settings(min_screenshots=value)
    with pytest.raises(ValueError):
        Settings(max_screenshots=value)


def test_min_cannot_exceed_max() -> None:
    with pytest.raises(ValueError, match="min_screenshots"):
        Settings(min_screenshots=5, max_screenshots=2)


def test_native_port_warns() -> None:
    with pytest.warns(UserWarning, match="native dev server"):
        Settings(port=8081)


def test_build_settings_converts_iterables() -> None:
    settings = build_settings(devices=["phone"], variants=["portrait"], exclude=("/debug",))
    assert settings.devices == ("phone",)
    assert settings.variants == ("portrait",)
    assert settings.exclude == ("/debug",)


def test_dpr_override() -> None:
    assert Settings(dpr_override=3).dpr_for(device()) == 3
