"""Static UI serving tests (M4.2 / M4.8)."""

from fastapi.testclient import TestClient

from yoruu.web.app import create_app

MOCK_PAGES = [
    "00_hud.html",
    "index.html",
    "01_dashboard.html",
    "02_trade_log.html",
    "03_nightly_review.html",
    "04_settings.html",
    "05_strategy_history.html",
    "06_alerts.html",
    "07_mode_switch.html",
    "08_emergency_stop.html",
    "09_markov_live.html",
    "10_what_if.html",
]


def test_root_redirects_to_hud() -> None:
    client = TestClient(create_app())
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (307, 302)
    assert resp.headers["location"] == "/pages/00_hud.html"


def test_static_assets_served() -> None:
    client = TestClient(create_app())
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/js/app.js").status_code == 200
    assert client.get("/static/js/sse-client.js").status_code == 200
    assert client.get("/static/locales/ja.bundle.js").status_code == 200


def test_all_mock_pages_served() -> None:
    client = TestClient(create_app())
    for page in MOCK_PAGES:
        resp = client.get(f"/pages/{page}")
        assert resp.status_code == 200, page
        assert "/static/css/style.css" in resp.text, page
        assert "/static/js/mock-data.js" in resp.text, page


def test_hud_page_has_hero_mount() -> None:
    client = TestClient(create_app())
    body = client.get("/pages/00_hud.html").text
    assert 'id="hud-hero"' in body
    assert "/static/js/sse-client.js" in body
