import json
from pathlib import Path

from PIL import Image

from store_shots.infrastructure.checker import check_dimensions


def make_output(root: Path, expected: tuple[int, int]) -> None:
    platform = root / "google-play"
    image = platform / "phone" / "portrait" / "01-home.png"
    image.parent.mkdir(parents=True)
    Image.new("RGB", (10, 20), "blue").save(image)
    (platform / "manifest.json").write_text(
        json.dumps(
            {
                "captures": [
                    {
                        "path": "google-play/phone/portrait/01-home.png",
                        "width": expected[0],
                        "height": expected[1],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_check_reports_ok(tmp_path: Path, capsys) -> None:
    make_output(tmp_path, (10, 20))
    assert check_dimensions(tmp_path) == 0
    assert "1 OK, 0 problem(s)" in capsys.readouterr().out


def test_check_reports_mismatch(tmp_path: Path, capsys) -> None:
    make_output(tmp_path, (20, 40))
    assert check_dimensions(tmp_path) == 1
    assert "MISMATCH" in capsys.readouterr().out


def test_check_without_manifests(tmp_path: Path) -> None:
    assert check_dimensions(tmp_path) == 1
