from store_shots.routes import RouteCrawler, slugify_route


def crawler() -> RouteCrawler:
    return RouteCrawler(page=None, base_url="http://127.0.0.1:19006")  # type: ignore[arg-type]


def test_slugify_route() -> None:
    assert slugify_route("/profile/settings?tab=1") == "profile-settings-tab-1"
    assert slugify_route("/") == "home"


def test_normalize_internal_links() -> None:
    assert crawler()._normalize("/settings") == "/settings"
    assert crawler()._normalize("settings?tab=2") == "/settings?tab=2"


def test_normalize_rejects_external_and_assets() -> None:
    subject = crawler()
    assert subject._normalize("https://example.com/other") is None
    assert subject._normalize("#section") is None
    assert subject._normalize("mailto:hi@example.com") is None
    assert subject._normalize("/assets/app.js") is None
    assert subject._normalize("/_expo/manifest") is None
