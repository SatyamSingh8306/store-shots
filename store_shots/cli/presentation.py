"""CLI output formatting (kept separate from command orchestration)."""

from __future__ import annotations

from typing import Any


def print_dry_run(summary: dict[str, Any]) -> None:
    """Print a preview of screens and capture targets."""
    print(f"Base URL: {summary['base_url']}")
    print(f"Screens ({len(summary['screens'])}):")
    for screen in summary["screens"]:
        print(f"  {screen}")
    for platform_id, info in summary["platforms"].items():
        print(f"\n{platform_id} - {info['label']}: {len(info['targets'])} targets")
        for target in info["targets"]:
            print(
                f"  {target['device']}/{target['variant']}  "
                f"{target['width']}x{target['height']}  "
                f"(captures {target['min_screenshots']}-{target['max_screenshots']})"
            )
    total = sum(len(info["targets"]) for info in summary["platforms"].values())
    print(f"\nTotal screenshots per route: {total}")


def print_summary(summary: dict[str, Any]) -> None:
    """Print the result of a capture run."""
    print(f"Base URL: {summary['base_url']}")
    print(f"Screens discovered: {len(summary['screens'])}")
    for screen in summary["screens"]:
        print(f"  - {screen}")
    for platform_id, info in summary["platforms"].items():
        print(
            f"  {info['label']:<20} {info['captures']:>3} screenshots "
            f"({info['targets']} sizes, {info['errors']} errors)"
        )
    print(f"\nTotal screenshots: {summary['captures']}")
    print(f"Errors: {summary['errors']}  Warnings: {summary['warnings']}")
    print(f"Output: {summary['output_dir']}")
    print("\nFolder tree:")
    for platform, devices in summary["tree"].items():
        print(f"  {platform}/")
        for files in devices.values():
            for file in files:
                print(f"    {file}")
