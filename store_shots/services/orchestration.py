"""Run the full capture workflow and write manifests and reports."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

from ..config.settings import Settings
from ..infrastructure.storage import OutputLayout
from ..infrastructure.validation import Issue
from ..profiles import iter_targets
from .capture import ViewportCapturer
from .discovery import RouteScreenDiscoverer, flow_to_shot


class CaptureOrchestrator:
    """Run discovery and all platform/device captures, then write reports."""

    def __init__(
        self,
        settings: Settings,
        output: OutputLayout,
        discoverer: RouteScreenDiscoverer,
        capturer: ViewportCapturer,
    ) -> None:
        self.settings = settings
        self.output = output
        self.discoverer = discoverer
        self.capturer = capturer

    def run(self) -> dict[str, Any]:
        from playwright.sync_api import sync_playwright

        settings = self.settings
        output = self.output
        output.prepare()
        self._stage("starting browser")

        with sync_playwright() as playwright:
            launch_options: dict[str, Any] = {"headless": settings.headless}
            if settings.browser_channel:
                launch_options["channel"] = settings.browser_channel
            try:
                browser = playwright.chromium.launch(**launch_options)
            except Exception as error:
                raise RuntimeError(
                    "Could not launch Chromium. Install it with: playwright install chromium"
                ) from error

            try:
                self._stage("discovering screens")
                flows = self.discoverer.discover(browser)
                shots = [flow_to_shot(flow) for flow in flows]
                shot_routes = [shot["route"] for shot in shots]
                self._stage(f"discovered {len(shots)} screens")

                if settings.dry_run:
                    self._stage("preview ready")
                    return self._dry_run_summary(shots, shot_routes)

                platform_summaries: dict[str, Any] = {}
                all_findings: list[dict[str, str | None]] = []
                total_captures = 0

                for platform in settings.platforms:
                    targets = list(
                        iter_targets(
                            platform, settings.devices, settings.variants, settings.recommended_only
                        )
                    )
                    self._stage(f"{platform.id}: preparing {len(targets)} targets")
                    captures: list[dict[str, Any]] = []
                    findings: list[dict[str, str | None]] = []
                    active_device_ids: list[str] = []
                    warned_min_devices: set[str] = set()

                    for target_index, (device, variant) in enumerate(targets, start=1):
                        self._stage(
                            f"{platform.id}/{device.id}/{variant.id}: "
                            f"target {target_index}/{len(targets)}"
                        )
                        if device.id not in active_device_ids:
                            active_device_ids.append(device.id)

                        max_allowed = settings.max_for(device)
                        min_required = settings.min_for(device)
                        selected_shots = shots[:max_allowed]
                        if len(selected_shots) < min_required and device.id not in warned_min_devices:
                            warned_min_devices.add(device.id)
                            findings.append(
                                Issue(
                                    "warning",
                                    "TOO_FEW_SCREENSHOTS",
                                    f"Only {len(selected_shots)} screen(s) discovered for "
                                    f"{device.id}; {min_required} per variant "
                                    "required/recommended.",
                                    str(output.platform_root(platform)),
                                ).as_dict()
                            )

                        for shot_index, shot in enumerate(selected_shots, start=1):
                            self._stage(
                                f"{device.id}/{variant.id}: "
                                f"{shot_index}/{len(selected_shots)} {shot['id']}"
                            )
                            url = urljoin(f"{settings.base_url}/", shot["route"].lstrip("/"))
                            record, issues = self._attempt_capture(
                                self.capturer.capture,
                                findings,
                                browser=browser,
                                platform=platform,
                                url=url,
                                shot=shot,
                                shot_index=shot_index,
                                device=device,
                                variant=variant,
                            )
                            captures.extend(record)
                            findings.extend(issue.as_dict() for issue in issues)

                    if shots:
                        self._stage(f"{platform.id}: capturing device assets")
                        first_shot = shots[0]
                        first_url = urljoin(f"{settings.base_url}/", first_shot["route"].lstrip("/"))
                        for device in platform.devices:
                            if device.id not in active_device_ids:
                                continue
                            for asset in device.extra_assets:
                                record, issues = self._attempt_capture(
                                    self.capturer.capture_asset,
                                    findings,
                                    browser=browser,
                                    platform=platform,
                                    url=first_url,
                                    shot=first_shot,
                                    asset=asset,
                                    device=device,
                                )
                                captures.extend(record)
                                findings.extend(issue.as_dict() for issue in issues)

                    if shots:
                        self._stage(f"{platform.id}: capturing platform assets")
                        first_shot = shots[0]
                        first_url = urljoin(f"{settings.base_url}/", first_shot["route"].lstrip("/"))
                        for asset in platform.extra_assets:
                            record, issues = self._attempt_capture(
                                self.capturer.capture_asset,
                                findings,
                                browser=browser,
                                platform=platform,
                                url=first_url,
                                shot=first_shot,
                                asset=asset,
                                device=None,
                            )
                            captures.extend(record)
                            findings.extend(issue.as_dict() for issue in issues)

                    manifest = {
                        "version": "1.0.0",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "platform": platform.id,
                        "source": {
                            "host": settings.host,
                            "port": settings.port,
                            "base_url": settings.base_url,
                            "routes": shot_routes,
                            "screens": [shot["id"] for shot in shots],
                        },
                        "limits": {
                            "min_screenshots": settings.min_screenshots_effective,
                            "max_screenshots": settings.max_screenshots_effective,
                            "full_page": settings.full_page,
                        },
                        "captures": captures,
                    }
                    self._stage(f"{platform.id}: writing manifest")
                    output.write_json("manifest.json", manifest, platform)

                    errors = sum(1 for item in findings if item["severity"] == "error")
                    warnings_count = sum(1 for item in findings if item["severity"] == "warning")
                    platform_summaries[platform.id] = {
                        "label": platform.label,
                        "folder": platform.folder,
                        "targets": len(targets),
                        "screens": len(shots),
                        "captures": len(captures),
                        "errors": errors,
                        "warnings": warnings_count,
                    }
                    total_captures += len(captures)
                    all_findings.extend(findings)

                self._stage("summarizing results")
                report = {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "captures": total_captures,
                    "errors": sum(1 for item in all_findings if item["severity"] == "error"),
                    "warnings": sum(1 for item in all_findings if item["severity"] == "warning"),
                    "findings": all_findings,
                }
                output.write_json(
                    "manifest.json",
                    {
                        "version": "1.0.0",
                        "generated_at": report["generated_at"],
                        "source": {
                            "host": settings.host,
                            "port": settings.port,
                            "base_url": settings.base_url,
                        },
                        "platforms": list(platform_summaries),
                        "routes": shot_routes,
                        "screens": [shot["id"] for shot in shots],
                    },
                )
                output.write_json("validation_report.json", report)

                return {
                    "dry_run": False,
                    "base_url": settings.base_url,
                    "output_dir": str(output.root),
                    "routes": shot_routes,
                    "screens": [shot["id"] for shot in shots],
                    "shots": shots,
                    "platforms": platform_summaries,
                    "captures": total_captures,
                    "errors": report["errors"],
                    "warnings": report["warnings"],
                    "tree": output.tree(),
                }
            finally:
                browser.close()

    def _attempt_capture(
        self, operation: Callable[..., tuple[dict[str, Any], list[Issue]]],
        findings: list[dict[str, str | None]],
        **kwargs: Any,
    ) -> tuple[list[dict[str, Any]], list[Issue]]:
        try:
            record, issues = operation(**kwargs)
        except Exception as error:
            device = kwargs.get("device")
            shot = kwargs.get("shot") or {}
            asset = kwargs.get("asset")
            if asset is not None:
                label = f"{getattr(device, 'id', 'platform')}/{asset.id}"
            else:
                label = f"{getattr(device, 'id', '?')}/{getattr(kwargs.get('variant'), 'id', '?')} {shot.get('id', '')}"
            findings.append(
                Issue("error", "CAPTURE_FAILED", f"{label}: {error}", None).as_dict()
            )
            self._tick()
            return [], []
        self._tick()
        return [record], issues

    def _dry_run_summary(
        self, shots: list[dict[str, Any]], shot_routes: list[str]
    ) -> dict[str, Any]:
        settings = self.settings
        return {
            "dry_run": True,
            "base_url": settings.base_url,
            "shots": shots,
            "routes": shot_routes,
            "screens": [shot["id"] for shot in shots],
            "min_screenshots": settings.min_screenshots_effective,
            "max_screenshots": settings.max_screenshots_effective,
            "full_page": settings.full_page,
            "platforms": {
                platform.id: {
                    "label": platform.label,
                    "targets": [
                        {
                            "device": device.id,
                            "variant": variant.id,
                            "width": variant.width,
                            "height": variant.height,
                            "css_viewport": self.capturer.css_viewport(device, variant),
                            "device_scale_factor": settings.dpr_for(device),
                            "min_screenshots": settings.min_for(device),
                            "max_screenshots": settings.max_for(device),
                        }
                        for device, variant in iter_targets(
                            platform,
                            settings.devices,
                            settings.variants,
                            settings.recommended_only,
                        )
                    ],
                }
                for platform in settings.platforms
            },
        }

    def _stage(self, text: str) -> None:
        progress = self.settings.progress
        if progress is not None:
            update = getattr(progress, "update", None)
            if update is not None:
                update(text)

    def _tick(self, count: int = 1) -> None:
        progress = self.settings.progress
        if progress is not None:
            tick = getattr(progress, "tick", None)
            if tick is not None:
                tick(count)
