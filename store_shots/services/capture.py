"""Capture screens and extra assets at exact device sizes."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser

from ..config.settings import Settings
from ..core.models import DeviceType, ExtraAsset, PlatformSpec, Variant
from ..flows import Step, run_steps
from ..infrastructure.storage import OutputLayout
from ..infrastructure.validation import Issue
from ..routes import slugify_route
from .settling import DefaultPageSettler

Validator = Callable[..., list[Issue]]


class ViewportCapturer:
    """Capture a screen or asset at the exact device viewport and size."""

    def __init__(
        self,
        settings: Settings,
        output: OutputLayout,
        settler: DefaultPageSettler,
        validator: Validator | None = None,
    ) -> None:
        self.settings = settings
        self.output = output
        self.settler = settler
        self.validator: Validator = validator or self._default_validator

    @staticmethod
    def _default_validator(
        target: Path,
        width: int,
        height: int,
        rules: Any,
        max_file_size_mb: float | None,
    ) -> list[Issue]:
        from ..infrastructure.validation import finalize_image

        return finalize_image(target, width, height, rules, max_file_size_mb)

    def css_viewport(
        self, device: DeviceType, variant: Variant, dpr: int | None = None
    ) -> dict[str, int]:
        scale = dpr if dpr is not None else self.settings.dpr_for(device)
        if variant.width % scale or variant.height % scale:
            raise ValueError(
                f"{device.id}/{variant.id}: {variant.width}x{variant.height} is not divisible "
                f"by css_dpr={scale}. Set a compatible css_dpr on the device profile."
            )
        return {"width": variant.width // scale, "height": variant.height // scale}

    def capture(
        self,
        *,
        browser: Browser,
        platform: PlatformSpec,
        url: str,
        shot: dict[str, Any],
        shot_index: int,
        device: DeviceType,
        variant: Variant,
        css_dpr: int | None = None,
        mobile_emulation: bool | None = None,
        path_parts: tuple[str, ...] | None = None,
        extra_asset: str | None = None,
    ) -> tuple[dict[str, Any], list[Issue]]:
        settings = self.settings
        dpr = css_dpr if css_dpr is not None else settings.dpr_for(device)
        css_viewport = self.css_viewport(device, variant, dpr=dpr)
        mobile = device.mobile_emulation if mobile_emulation is None else mobile_emulation
        full_page_info = {"mode": "never", "detected": False, "enabled": False}

        context = browser.new_context(
            viewport=css_viewport,
            device_scale_factor=dpr,
            is_mobile=mobile,
            has_touch=mobile,
            ignore_https_errors=True,
        )
        try:
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=settings.navigation_timeout_ms)
            self.settler.settle(page)

            steps = tuple(Step.from_dict(item) for item in shot["steps"])
            action_log: list[str] = []
            for step in steps:
                try:
                    action_log.extend(run_steps(page, [step]))
                except Exception as error:
                    raise RuntimeError(
                        f"Flow '{shot['id']}' failed at {step.action} '{step.value}': {error}"
                    ) from error

            if steps:
                self.settler.settle(page, network_idle_timeout_ms=2500)

            target = self._target(
                platform, shot, shot_index, device, variant, path_parts
            )
            page.screenshot(
                path=str(target),
                full_page=False,
                animations="disabled",
                caret="hide",
            )
            issues = self.validator(
                target,
                variant.width,
                variant.height,
                platform.rules,
                device.max_file_size_mb,
            )
        finally:
            context.close()

        record: dict[str, Any] = {
            "route": shot["route"],
            "scene": shot["id"],
            "platform": platform.id,
            "device": device.id,
            "variant": variant.id,
            "width": variant.width,
            "height": variant.height,
            "css_viewport": css_viewport,
            "device_scale_factor": dpr,
            "mobile_emulation": mobile,
            "actions": action_log,
            "full_page": full_page_info,
            "path": str(target.relative_to(self.output.root)).replace("\\", "/"),
            "issues": [issue.as_dict() for issue in issues],
        }
        if extra_asset:
            record["asset"] = extra_asset
        return record, issues

    def capture_asset(
        self,
        *,
        browser: Browser,
        platform: PlatformSpec,
        url: str,
        shot: dict[str, Any],
        asset: ExtraAsset,
        device: DeviceType | None,
    ) -> tuple[dict[str, Any], list[Issue]]:
        variant = Variant(
            id=asset.id,
            label=asset.label,
            orientation="landscape",
            aspect_ratio="",
            width=asset.width,
            height=asset.height,
        )
        if device is None:
            pseudo_device = DeviceType(
                id="platform",
                label=asset.label,
                variants=(),
                css_dpr=1,
                mobile_emulation=False,
            )
            path_parts: tuple[str, ...] = (asset.id,)
        else:
            pseudo_device = device
            path_parts = (device.id, asset.id)

        return self.capture(
            browser=browser,
            platform=platform,
            url=url,
            shot=shot,
            shot_index=1,
            device=pseudo_device,
            variant=variant,
            css_dpr=1,
            mobile_emulation=False,
            path_parts=path_parts,
            extra_asset=asset.id,
        )

    def _target(
        self,
        platform: PlatformSpec,
        shot: dict[str, Any],
        shot_index: int,
        device: DeviceType,
        variant: Variant,
        path_parts: tuple[str, ...] | None,
    ) -> Path:
        slug = slugify_route(shot["id"])
        if path_parts:
            target = self.output.asset_path(
                platform, *path_parts, route_slug=slug, route_index=shot_index
            )
        else:
            target = self.output.capture_path(
                platform,
                device.id,
                variant.id,
                slug,
                shot_index,
                extension="png",
            )
        if target.exists() and not self.settings.overwrite:
            suffix = int(datetime.now(timezone.utc).timestamp() * 1000)
            target = target.with_name(f"{target.stem}-{suffix}{target.suffix}")
        return target
