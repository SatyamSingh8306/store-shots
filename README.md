# store-shots

[![CI](https://github.com/SatyamSingh8306/store-shots/actions/workflows/ci.yml/badge.svg)](https://github.com/SatyamSingh8306/store-shots/actions/workflows/ci.yml)

A Python library + CLI that connects to a running **Expo web dev server**, discovers every screen automatically (following links **and** clicking buttons/tabs), screenshots each screen at the required sizes for **multiple app stores**, and saves the images in the correct folder structure for each platform.

**Author:** Satyam Singh · <satyamsingh7734@gmail.com>

**Documentation site:** [`docs/`](docs/) — deployable to GitHub Pages with `.github/workflows/docs.yml`.

```python
from store_shots import ExpoShotter

shotter = ExpoShotter(
    host="127.0.0.1",     # Expo web host
    port=19006,           # Expo web port
    output_dir="./store-assets",
    platforms=["playstore", "appstore"],
)
summary = shotter.run()
```

Built-in presets: **Google Play**, **Apple App Store**, **Amazon Appstore** — plus custom `PlatformSpec` objects for any other store.

---

## Requirements

- Python 3.10+
- Expo project with web support: `npx expo start --web`
- Playwright Chromium (installed once)

```bash
pip install store-shots
python -m playwright install chromium
```

> Expo Go is a native host with no HTTP page a browser can capture. This tool targets the **web build of the same Expo project** (`expo start --web`), which is why it only needs `host` + `port`.

---

## Development

From a checkout, install the package in editable mode with the dev extras:

```bash
pip install -e ".[dev]"
python -m pytest -q
python -m ruff check store_shots tests
```

CI runs `ruff check` and `pytest` on pushes and pull requests to `main`, across Python 3.10–3.13. See `.github/workflows/ci.yml`.

---

## Architecture

The package is organized into folders by responsibility and uses protocols so each layer can be replaced or tested independently:

```text
store_shots/
├── client.py            # thin ExpoShotter facade
├── flows.py             # replayable interaction steps
├── profiles.py          # target iteration
├── routes.py            # link/button screen crawler
├── version.py
├── core/                # models.py (data classes), protocols.py (interfaces)
├── config/              # settings.py (validated Settings + build_settings)
├── services/            # settling.py, discovery.py, capture.py, orchestration.py
├── infrastructure/      # storage.py, validation.py, waits.py, progress.py, checker.py
├── cli/                 # app.py (parser/dispatch), presentation.py (output)
└── platforms/           # playstore.py, appstore.py, amazon.py
```

`store_shots.common` and `store_shots.settings` remain as compatibility shims. `ExpoShotter` keeps its original constructor and public attributes, but no longer contains orchestration logic. You can use the services directly with your own implementations by satisfying the protocols in `store_shots.core.protocols`.

---

## CLI

```bash
store-shots --host 127.0.0.1 --port 19006 --output-dir ./store-assets
# or
python -m store_shots --host 127.0.0.1 --port 19006 --output-dir ./store-assets
```

Common options:

```bash
# List all built-in platform presets and their sizes
store-shots --list-platforms

# Pick platforms
store-shots --platform playstore --platform appstore
store-shots --platform appstore --device iphone-63 --recommended-only

# Preview screens + targets without taking screenshots
store-shots --dry-run

# Verify generated images against the required dimensions
store-shots --check --output-dir ./store-assets

# How many screenshots to capture per device/variant
store-shots --screens 6                  # exactly 6 (sets min and max)
store-shots --min-screenshots 4 --max-screenshots 8

# Screen discovery: links + buttons/tabs (default), or links only
store-shots --max-routes 30 --max-depth 4 --max-actions 32
store-shots --no-click-buttons

# Explicit routes instead of discovery
store-shots --route / --route /settings --route /profile

# Discovery/wait tuning
store-shots --exclude /debug --wait-ms 1200
store-shots --wait-for-selector '[data-testid="app-ready"]'
store-shots --no-wait-for-loading

# Visible browser, overwrite existing images
store-shots --headed --overwrite
```

Run `store-shots --help` for the full option list.

### Progress display

The CLI reports stages as it works, for example `[..] discovering screens`, `[..] phone/portrait: 1/2 home`, and `[..] playstore: writing manifest`. When output is redirected (logs, CI) it prints one plain line per stage.

In a real terminal the current stage animates in place using **alive-progress** (installed as a required dependency). The bar advances once per captured image and shows rate, elapsed time and the current stage text. The `classic` ASCII theme is used — no emojis. If stdout is redirected (logs, CI) the bar is disabled and one plain `[..]` line per stage is printed instead; a small built-in `|/-\` spinner is used only if `alive-progress` is unavailable. Failures print `[fail] <message>`.

---

## Python API

```python
from store_shots import ExpoShotter, describe

print(describe())

shotter = ExpoShotter(
    host="192.168.1.20",
    port=19006,
    output_dir="./store-assets",
    platforms=["playstore", "appstore", "amazon"],  # None = all built-ins
    scheme="http",
    base_path="",
    devices=["phone", "ipad-13"],   # None = all devices of every platform
    variants=["portrait"],          # None = all variants
    recommended_only=False,
    # routes=[...],                 # skip auto screen discovery
    click_buttons=True,             # follow links AND click buttons/tabs
    max_routes=25,
    max_depth=3,
    max_actions_per_screen=24,
    exclude=("/debug", "/admin"),
    # screens=6,                    # exact count (sets min and max)
    # min_screenshots=4,            # warn when fewer screens are found
    # max_screenshots=8,            # cap screenshots per device/variant
    wait_ms=900,
    wait_for_loading=True,
    headless=True,
    overwrite=False,
)

summary = shotter.run()
print(summary["captures"], "screenshots saved to", summary["output_dir"])
```

| Argument | Default | Purpose |
| --- | --- | --- |
| `host` / `port` | `127.0.0.1` / `19006` | Expo web server address |
| `output_dir` | `store-assets` | Root of the generated folder trees |
| `scheme` / `base_path` | `http` / `""` | URL scheme / optional subpath |
| `platforms` | all built-ins | Platform ids **or** custom `PlatformSpec` objects |
| `devices` / `variants` | all | Filter target form factors |
| `recommended_only` | `False` | Skip optional variants |
| `routes` | auto | Explicit route list; disables discovery |
| `click_buttons` | `True` | Click buttons/tabs while discovering screens |
| `max_routes` / `max_depth` | `25` / `3` | Discovery limits (screens / click depth) |
| `max_actions_per_screen` | `24` | Buttons/tabs inspected per screen |
| `screens` | `None` | Exact screenshots per device/variant (sets min and max) |
| `min_screenshots` / `max_screenshots` | profile | Warn below / cap above this count |
| `exclude` | `()` | Substrings skipped during discovery |
| `wait_ms` | `700` | Extra settle time before each capture |
| `wait_for_loading` | `True` | Wait for spinners/loading placeholders to disappear |
| `full_page` / `full_page_fit` | ignored | Deprecated; screenshots always use the exact device viewport |
| `wait_for_selector` | `None` | CSS selector to wait for |
| `headless` | `True` | Chromium visibility |
| `browser_channel` | `None` | e.g. `chrome` |
| `overwrite` / `dry_run` | `False` | File handling / preview mode |

---

## Custom platform (or "and more")

Add any store by passing your own `PlatformSpec`:

```python
from store_shots import ExpoShotter, PlatformSpec, GlobalRules, DeviceType, Variant

my_store = PlatformSpec(
    id="my-store",
    label="My Store",
    output_folder="my-store",
    rules=GlobalRules(min_dimension_px=320, max_dimension_px=4096),
    devices=(
        DeviceType(
            id="phone",
            label="Phone",
            variants=(Variant("portrait", "Portrait", "portrait", "9:16", 1080, 1920),),
        ),
    ),
)

ExpoShotter(platforms=[my_store], output_dir="./store-assets").run()
```

Or add it to `store_shots/platforms/PLATFORMS` to make it selectable from the CLI.

---

## How screens are discovered

Starting at `/`, the explorer loads the page and does a breadth-first search over **both**:

1. every internal `<a href>` (Expo Router `<Link>` renders these), and
2. every visible button, tab, `role=button`/`role=tab`, plus React Native Web `Pressable`/`TouchableOpacity` divs (detected by pointer cursor or `tabindex`, even without an ARIA role).

For a button/tab, it records the click path from the app root (for example `Start training → Exercises`) and replays that path before the screenshot. Each screen is identified by its URL plus a signature of its headings/visible text, so the same screen reached two ways is only captured once. Destructive actions (log out, delete, purchase, …) are skipped. External URLs, fragments, assets, `/_expo`, `/assets` and excluded substrings are ignored.

Limits: `--max-routes` (screens), `--max-depth` (click depth) and `--max-actions` (buttons/tabs inspected per screen, default 24). The CLI now lists every discovered screen with its id; `manifest.json` records the exact click path used to reach each one. Pass `routes=[...]` or `--route` to skip discovery, or `--no-click-buttons` to follow links only. If onboarding requires filling fields before a button becomes active, use a flow file (see below) — the explorer clicks buttons but does not type into forms.

## How many screenshots per device

Store profiles define `min_screenshots` / `max_screenshots` (Google Play: 2–8 for phones, at least 4 for tablets/Chromebooks, 3–8 for foldables, 4–8 for XR). Override them globally:

```bash
store-shots --screens 6                       # exactly 6 per device/variant
store-shots --min-screenshots 4 --max-screenshots 8
```

When fewer screens are discovered than the minimum, a `TOO_FEW_SCREENSHOTS` warning is added to `validation_report.json` instead of failing the run. Extra required images (Android TV banner, Google Play feature graphic) are always captured once at their exact size.

---

## Screen flows and avoiding loading screenshots

A fixed delay is not enough for real apps. Before every capture the tool waits for `document.readyState === 'complete'`, `networkidle`, `document.fonts.ready`, all images, visible loading spinners/placeholders to disappear, and the DOM to stop mutating. After running flow steps it settles again, so a screen is never captured mid-transition:

```bash
store-shots --host 127.0.0.1 --port 8081 --wait-for-text "No session in progress"
```

For screens behind onboarding or a sequence that automatic exploration cannot reach, pass a JSON flow file. Each flow is a screen with a route and a list of actions executed before the screenshot:

```bash
store-shots --host 127.0.0.1 --port 8081 \
  --flows examples/replog-flows.json \
  --platform playstore --device phone --recommended-only
```

Supported actions: `fill` (by input placeholder), `click_text`, `click_selector`, `wait_for_text`, `wait_text_gone`, `wait_for_selector`, `wait_ms`, `scroll`, `press`. See `examples/replog-flows.json` for a complete onboarding → home / split / exercises / progress example. The resolved action log is recorded in `manifest.json` for each capture.

## Responsive capture (device emulation)

Screenshots are taken with Chrome device emulation, not by stretching a desktop-sized viewport. Each device profile defines `css_dpr`; the browser viewport is `target_px / css_dpr` with `device_scale_factor = css_dpr`:

| Target | CSS viewport | DPR | Output |
| --- | --- | --- | --- |
| Phone portrait | 540×960 | 2 | 1080×1920 |
| Phone landscape | 960×540 | 2 | 1920×1080 |
| 7″ tablet portrait | 600×960 | 2 | 1200×1920 |
| 10″ tablet portrait | 800×1280 | 2 | 1600×2560 |
| Foldable square | 960×960 | 2 | 1920×1920 |
| Desktop / laptop | 1920×1080 | 1 | 1920×1080 |
| Android TV | 1920×1080 | 1 | 1920×1080 |
| Android XR | 1920×1200 | 2 | 3840×2400 |
| Wear OS | 240×240 | 2 | 480×480 |
| iPhone 6.3″ | 603×1311 | 2 | 1206×2622 |
| iPad 13″ | 1032×1376 | 2 | 2064×2752 |

Large-screen profiles (desktop, Chromebook, TV, automotive) use DPR 1 so the app renders its real desktop/large-screen layout instead of a zoomed mobile one. DPR 2 fits a full phone/tablet screen with readable text. Use `--dpr 3` for a more zoomed-in phone look, or `--dpr 1` to show more CSS content (this changes the app's responsive layout).

Phone/watch profiles also enable mobile emulation (touch + mobile viewport meta handling). The resolved `css_viewport` / `device_scale_factor` are recorded in each platform's `manifest.json`. Change `css_dpr` in `store_shots/platforms/*.py` to tune a profile (dimensions must divide evenly).

## Output folder structure

```
store-assets/
├── google-play/
│   ├── phone/{portrait,landscape,square}/01-home.png ...
│   ├── foldable/{square,wide,outer,outer-landscape}/...
│   ├── tablet-7/{portrait,landscape}/...
│   ├── tablet-10/{portrait,landscape}/...
│   ├── chromebook/{landscape,portrait}/...
│   ├── desktop/{landscape,wide}/...
│   ├── android-tv/landscape/... + android-tv/banner/01-home.png
│   ├── wear-os/square/...
│   ├── automotive/{portrait,landscape}/...
│   ├── android-xr/wide/...
│   ├── feature-graphic/01-home.png
│   └── manifest.json
├── app-store/
│   ├── iphone-63/portrait/01-home.png ...
│   ├── iphone-69/portrait/...
│   ├── ipad-13/portrait/...
│   ├── apple-watch/square/...
│   └── manifest.json
├── amazon-appstore/
│   ├── phone/...
│   ├── tablet/...
│   ├── fire-tv/...
│   └── manifest.json
├── manifest.json
└── validation_report.json
```

Each screenshot is named `<NN>-<route-slug>.png` (e.g. `02-profile-settings.png`). All images are normalized to **24-bit PNG with no alpha**; scrollbars, animations and carets are hidden, and every image is captured at the exact target dimension.

### Screens taller than the viewport

Full-page expansion has been removed. Expanding the page and stretching the result changed the app's responsive layout and distorted screenshots (for example, game screens rendered as a narrow column with blank space on the right). Every capture — including the Android TV banner and the Google Play feature graphic — now uses the exact device viewport from the platform profile, with no DPR change, scaling, or letterboxing.

If a screen needs content below the fold visible in the screenshot, use a flow file with a `scroll` action to bring that content into the viewport before capture. `--dpr 1` shows more CSS content but changes the app's responsive layout, so it is not applied automatically.

`manifest.json` records `full_page: {"mode": "never", "detected": false, "enabled": false}` for backwards compatibility; no fit metadata is produced.

Run `store-shots --check --output-dir ./store-assets` to print every image's actual size next to its required size and flag missing or mismatched files. `store-shots --list-platforms` prints all required dimensions.

`manifest.json` files record the source URL, discovered screens (including the click path used to reach each one), and every capture with its path and validation issues. `validation_report.json` summarizes errors/warnings (size mismatch, alpha removal, file size, too few screenshots, …).

---

## Built-in target sizes

### Google Play
Source: [Play Console preview assets](https://support.google.com/googleplay/android-developer/answer/9866151) (checked 2026).

| Device | Variants | Screenshots |
| --- | --- | --- |
| Phone | 1080×1920, 1920×1080, 1080×1080 | 2–8 |
| Foldable | 1920×1920 (1:1), 2560×1920 (4:3), 1080×1728 (10:16), 1728×1080 (16:10) | 3–8 |
| 7″ tablet | 1200×1920, 1920×1200 | 4–8 |
| 10″ tablet | 1600×2560, 2560×1600 | 4–8 |
| Chromebook | 1920×1080, 1080×1920 | 4–8 |
| Desktop / laptop | 1920×1080, 2560×1440 | 4–8 |
| Android TV | 1920×1080 + 1280×720 banner | 1–8 |
| Wear OS | 480×480 | 1–8 |
| Automotive | 800×1280, 1024×768 | 2–8 per variant |
| Android XR | 3840×2400 (8:5, min 1920×1200) | 4–8 |
| Feature graphic | 1024×500 | required |

Play limits: PNG/JPEG, 24-bit PNG with no alpha, each side 320–3,840 px, up to 8 MB per image, aspect ratio ≤ 2.3:1 for phone/tablet screenshots, and at least 2 screenshots across device types.

> Play Console calls its large-screen category **Chromebook**. The `desktop` preset is an extra 16:9 preset for web/desktop store listings; use it for the Chromebook/large-screen section if your app supports it.

### Apple App Store
| Device | Variants |
| --- | --- |
| iPhone 6.3″ (required) | 1206×2622, 2622×1206 |
| iPhone 6.9″ | 1320×2868, 2868×1320 |
| iPad 13″ | 2064×2752, 2752×2064 |
| Apple Watch Ultra | 422×514 |

### Amazon Appstore
| Device | Variants |
| --- | --- |
| Phone | 1080×1920, 1920×1080 |
| Fire tablet | 1280×800, 800×1280 |
| Fire TV | 1920×1080 |

Validation rules are per platform (min/max pixels, aspect ratio, file size, screenshot count). Edit the files in `store_shots/platforms/` to change any preset.
