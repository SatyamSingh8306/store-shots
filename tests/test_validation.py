from pathlib import Path

from PIL import Image

from store_shots.core.models import GlobalRules
from store_shots.infrastructure.validation import finalize_image


def test_alpha_is_removed(tmp_path: Path) -> None:
    path = tmp_path / "shot.png"
    Image.new("RGBA", (8, 8), (10, 20, 30, 128)).save(path)

    issues = finalize_image(path, 8, 8, GlobalRules())

    assert any(issue.code == "ALPHA_REMOVED" for issue in issues)
    with Image.open(path) as image:
        assert image.mode == "RGB"


def test_size_mismatch_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "shot.png"
    Image.new("RGB", (8, 8), "white").save(path)

    issues = finalize_image(path, 10, 8, GlobalRules())

    assert any(issue.code == "SIZE_MISMATCH" for issue in issues)


def test_valid_image_has_no_errors(tmp_path: Path) -> None:
    path = tmp_path / "shot.png"
    Image.new("RGB", (8, 8), "white").save(path)

    issues = finalize_image(path, 8, 8, GlobalRules(min_dimension_px=1))

    assert not [issue for issue in issues if issue.severity == "error"]
