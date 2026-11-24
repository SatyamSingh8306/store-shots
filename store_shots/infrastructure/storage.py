"""Output folder architecture and manifest writing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.models import PlatformSpec


class OutputLayout:
    """Maps captures into one folder tree per store platform.

    output_dir/
        <platform.folder>/
            <device-id>/
                <variant-id>/
                    <NN>-<route-slug>.png
            manifest.json
        manifest.json
        validation_report.json
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def prepare(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def platform_root(self, platform: PlatformSpec) -> Path:
        path = self.root / platform.folder
        path.mkdir(parents=True, exist_ok=True)
        return path

    def capture_path(
        self,
        platform: PlatformSpec,
        device_id: str,
        variant_id: str,
        route_slug: str,
        route_index: int,
        extension: str = "png",
    ) -> Path:
        folder = self.platform_root(platform) / device_id / variant_id
        folder.mkdir(parents=True, exist_ok=True)
        name = f"{route_index:02d}-{route_slug}.{extension.lstrip('.')}"
        return folder / name

    def asset_path(
        self,
        platform: PlatformSpec,
        *parts: str,
        route_slug: str,
        route_index: int,
        extension: str = "png",
    ) -> Path:
        """Path for a required extra asset, e.g. platform/device/banner/01-home.png."""
        folder = self.platform_root(platform).joinpath(*parts)
        folder.mkdir(parents=True, exist_ok=True)
        name = f"{route_index:02d}-{route_slug}.{extension.lstrip('.')}"
        return folder / name

    def write_json(
        self, name: str, payload: Any, platform: PlatformSpec | None = None
    ) -> Path:
        base = self.platform_root(platform) if platform else self.root
        base.mkdir(parents=True, exist_ok=True)
        path = base / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def tree(self) -> dict[str, dict[str, list[str]]]:
        """Snapshot of generated files: {platform: {device: [relative files]}}."""
        result: dict[str, dict[str, list[str]]] = {}
        if not self.root.exists():
            return result

        for platform_dir in sorted(self.root.iterdir()):
            if not platform_dir.is_dir():
                continue
            devices: dict[str, list[str]] = {}
            for device_dir in sorted(platform_dir.iterdir()):
                if not device_dir.is_dir():
                    continue
                files: list[str] = []
                for entry in sorted(device_dir.iterdir()):
                    if entry.is_file():
                        files.append(str(entry.relative_to(platform_dir)).replace("\\", "/"))
                        continue
                    if not entry.is_dir():
                        continue
                    files.extend(
                        str(file.relative_to(platform_dir)).replace("\\", "/")
                        for file in sorted(entry.iterdir())
                        if file.is_file()
                    )
                devices[device_dir.name] = files
            result[platform_dir.name] = devices
        return result
