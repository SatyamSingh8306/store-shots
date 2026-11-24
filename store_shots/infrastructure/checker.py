"""Verify generated images against the sizes recorded in their manifests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image


def check_dimensions(output_dir: str | Path) -> int:
    """Print actual vs required dimensions for every generated image."""
    root = Path(output_dir)
    manifests = sorted(root.glob("*/manifest.json"))
    if not manifests:
        print(f"error: no platform manifests found in {root}", file=sys.stderr)
        return 1

    checked = 0
    problems = 0
    print(f"{'file'.ljust(52)} {'actual'.rjust(11)} {'required'.rjust(11)}  status")
    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as error:
            print(f"error: cannot read {manifest_path}: {error}", file=sys.stderr)
            problems += 1
            continue

        for capture in manifest.get("captures", []):
            rel = str(capture.get("path", ""))
            expected = (int(capture["width"]), int(capture["height"]))
            path = root / rel
            actual = (0, 0)
            if not path.exists():
                status = "MISSING"
            else:
                try:
                    with Image.open(path) as image:
                        actual = image.size
                except Exception as error:
                    status = f"UNREADABLE: {error}"
                else:
                    status = "OK" if actual == expected else "MISMATCH"
            if status != "OK":
                problems += 1
            checked += 1
            print(
                f"{rel.ljust(52)} "
                f"{f'{actual[0]}x{actual[1]}'.rjust(11)} "
                f"{f'{expected[0]}x{expected[1]}'.rjust(11)}  {status}"
            )

    print(f"\nChecked {checked} images: {checked - problems} OK, {problems} problem(s).")
    return 1 if problems else 0
