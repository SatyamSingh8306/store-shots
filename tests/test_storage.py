import json
from pathlib import Path

from store_shots.core.models import PlatformSpec
from store_shots.infrastructure.storage import OutputLayout


def platform() -> PlatformSpec:
    return PlatformSpec(id="playstore", label="Play", devices=(), output_folder="google-play")


def test_capture_path_and_tree(tmp_path: Path) -> None:
    layout = OutputLayout(tmp_path / "assets")
    path = layout.capture_path(platform(), "phone", "portrait", "home", 2)
    path.write_bytes(b"png")
    path.parent.parent.joinpath("01-home.png").write_bytes(b"png")

    assert path.name == "02-home.png"
    assert path.parent.name == "portrait"
    tree = layout.tree()
    assert "google-play" in tree
    assert "phone" in tree["google-play"]
    assert any("02-home.png" in item for item in tree["google-play"]["phone"])


def test_asset_path(tmp_path: Path) -> None:
    layout = OutputLayout(tmp_path / "assets")
    path = layout.asset_path(platform(), "android-tv", "banner", route_slug="home", route_index=1)
    assert path.relative_to(layout.root).as_posix() == "google-play/android-tv/banner/01-home.png"


def test_write_json(tmp_path: Path) -> None:
    layout = OutputLayout(tmp_path / "assets")
    path = layout.write_json("manifest.json", {"ok": True}, platform())
    assert json.loads(path.read_text(encoding="utf-8")) == {"ok": True}
