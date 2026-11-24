from pathlib import Path

import pytest

from store_shots.config.settings import Settings
from store_shots.core.models import DeviceType, Variant
from store_shots.flows import CaptureFlow, Step
from store_shots.infrastructure.storage import OutputLayout
from store_shots.services import DefaultPageSettler, ViewportCapturer, flow_to_shot


def device() -> DeviceType:
    return DeviceType(
        id="phone",
        label="Phone",
        variants=(Variant("portrait", "Portrait", "portrait", "9:16", 1080, 1920),),
    )


def capturer(tmp_path: Path) -> ViewportCapturer:
    settings = Settings()
    return ViewportCapturer(settings, OutputLayout(tmp_path), DefaultPageSettler(settings))


def test_flow_to_shot() -> None:
    flow = CaptureFlow(id="home", route="/", steps=(Step("wait_for_text", "Ready", exact=True),))
    shot = flow_to_shot(flow)
    assert shot["id"] == "home"
    assert shot["route"] == "/"
    assert shot["steps"] == [{"action": "wait_for_text", "value": "Ready", "value2": None, "exact": True, "timeout_ms": 30000}]


def test_css_viewport() -> None:
    variant = device().variants[0]
    assert capturer(Path(".")).css_viewport(device(), variant) == {"width": 540, "height": 960}


def test_css_viewport_rejects_undivisible_size() -> None:
    bad = Variant("bad", "Bad", "portrait", "?", 1001, 1920)
    with pytest.raises(ValueError, match="not divisible"):
        capturer(Path(".")).css_viewport(device(), bad)
