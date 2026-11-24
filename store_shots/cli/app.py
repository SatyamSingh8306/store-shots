"""Command line interface: python -m store_shots [options]."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from ..client import ExpoShotter
from ..flows import load_flows
from ..infrastructure.checker import check_dimensions
from ..infrastructure.progress import StageProgress
from ..platforms import describe
from ..version import __version__
from .presentation import print_dry_run, print_summary

_PLATFORM_IDS = "playstore, appstore, amazon"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="store-shots",
        description=(
            "Capture an Expo web app at each store's required screenshot sizes and save "
            "the images in the correct folder structure for Google Play, App Store, and more."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  store-shots --host 127.0.0.1 --port 19006 --output-dir ./store-assets\n"
            "  store-shots --platform playstore --platform appstore\n"
            "  store-shots --platform playstore --screens 6\n"
            "  store-shots --check --output-dir ./store-assets\n"
            "  store-shots --platform appstore --device iphone-63 --recommended-only\n"
            "  store-shots --route / --route /settings --dry-run\n"
        ),
    )
    parser.add_argument("--host", default="127.0.0.1", help="Expo web host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=19006, help="Expo web port (default: 19006)")
    parser.add_argument(
        "--output-dir",
        default="store-assets",
        help="Directory to write the folder trees into (default: ./store-assets)",
    )
    parser.add_argument("--scheme", default="http", help="URL scheme (default: http)")
    parser.add_argument("--base-path", default="", help="Base path if app is served in a subfolder")
    parser.add_argument(
        "--platform",
        action="append",
        dest="platforms",
        metavar="ID",
        help=f"Store platform to capture, repeatable ({_PLATFORM_IDS}). Default: all",
    )
    parser.add_argument(
        "--device", action="append", dest="devices", help="Device id to capture, repeatable (default: all)"
    )
    parser.add_argument(
        "--variant", action="append", dest="variants", help="Variant id to capture, repeatable (default: all)"
    )
    parser.add_argument(
        "--recommended-only", action="store_true", help="Skip optional variants (e.g. landscape iPhone)"
    )
    parser.add_argument(
        "--dpr", type=int, default=None,
        help="Override device scale factor for all targets (2 fits full screens, 1 is tiny, 3 is zoomed)",
    )
    parser.add_argument(
        "--route", action="append", dest="routes", help="Explicit route, repeatable (disables crawl)"
    )
    parser.add_argument(
        "--flows", metavar="JSON", help="JSON file with interaction flows (screens reached by clicking/filling)"
    )
    parser.add_argument(
        "--wait-for-text", help="Wait until this text is visible before each capture"
    )
    parser.add_argument(
        "--no-network-idle", action="store_true", help="Skip the network-idle wait before capture"
    )
    parser.add_argument(
        "--max-routes", type=int, default=25, help="Max screens to discover (default: 25)"
    )
    parser.add_argument("--max-depth", type=int, default=3, help="Link/click crawl depth (default: 3)")
    parser.add_argument(
        "--exclude", action="append", default=[], help="Substring to skip in routes, repeatable"
    )
    parser.add_argument(
        "--screens",
        type=int,
        default=None,
        metavar="N",
        help="Capture exactly N screens per device/variant (sets and overrides min/max)",
    )
    parser.add_argument(
        "--min-screenshots",
        type=int,
        default=None,
        metavar="N",
        help="Minimum screenshots expected per device/variant (warn below this)",
    )
    parser.add_argument(
        "--max-screenshots",
        type=int,
        default=None,
        metavar="N",
        help="Maximum screenshots captured per device/variant (default: profile value)",
    )
    parser.add_argument(
        "--no-click-buttons",
        action="store_true",
        help="Only follow links; do not click buttons/tabs while discovering screens",
    )
    parser.add_argument(
        "--max-actions",
        type=int,
        default=24,
        metavar="N",
        help="Max buttons/tabs to inspect per discovered screen (default: 24)",
    )
    parser.add_argument(
        "--no-wait-for-loading",
        action="store_true",
        help="Do not wait for loading spinners/placeholders to disappear",
    )
    parser.add_argument(
        "--full-page",
        nargs="?",
        const="always",
        default="never",
        choices=("auto", "always", "never"),
        metavar="MODE",
        help=(
            "Deprecated and ignored: screenshots always use the exact device "
            "viewport, since expanding the page distorted app layouts"
        ),
    )
    parser.add_argument(
        "--full-page-fit",
        choices=("stretch", "contain"),
        default="stretch",
        help="Deprecated and ignored (full-page capture is disabled)",
    )
    parser.add_argument("--wait-ms", type=int, default=700, help="Settle time after load (default: 700)")
    parser.add_argument(
        "--wait-for-selector", default=None, help="Wait for this CSS selector before capturing"
    )
    parser.add_argument(
        "--navigation-timeout-ms", type=int, default=30000, help="Page navigation timeout"
    )
    parser.add_argument("--headed", action="store_true", help="Run Chromium in headed mode")
    parser.add_argument(
        "--browser-channel", default=None, help="Playwright browser channel, e.g. chrome"
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing screenshots")
    parser.add_argument(
        "--dry-run", action="store_true", help="List routes and targets without capturing"
    )
    parser.add_argument(
        "--list-platforms", action="store_true", help="Print all platform presets and exit"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify captured image dimensions against the required sizes and exit",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_platforms:
        print(describe())
        return 0

    if args.check:
        return check_dimensions(args.output_dir)

    progress = StageProgress()
    try:
        shotter = ExpoShotter(
            host=args.host,
            port=args.port,
            output_dir=args.output_dir,
            scheme=args.scheme,
            base_path=args.base_path,
            platforms=args.platforms,
            devices=args.devices,
            variants=args.variants,
            recommended_only=args.recommended_only,
            routes=args.routes,
            flows=load_flows(args.flows) if args.flows else None,
            wait_for_text=args.wait_for_text,
            network_idle=not args.no_network_idle,
            max_routes=args.max_routes,
            max_depth=args.max_depth,
            exclude=args.exclude,
            click_buttons=not args.no_click_buttons,
            max_actions_per_screen=args.max_actions,
            screens=args.screens,
            min_screenshots=args.min_screenshots,
            max_screenshots=args.max_screenshots,
            wait_for_loading=not args.no_wait_for_loading,
            full_page=args.full_page,
            full_page_fit=args.full_page_fit,
            wait_ms=args.wait_ms,
            navigation_timeout_ms=args.navigation_timeout_ms,
            wait_for_selector=args.wait_for_selector,
            headless=not args.headed,
            browser_channel=args.browser_channel,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            dpr_override=args.dpr,
            progress=progress,
        )
        summary = shotter.run()
    except Exception as error:
        progress.fail(str(error))
        return 1

    progress.finish("done")

    if summary["dry_run"]:
        print_dry_run(summary)
        return 0

    print_summary(summary)
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
