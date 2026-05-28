"""Static UI serving tests (M4.2)."""

from fastapi.testclient import TestClient

from yoruu.web.app import create_app


def test_root_redirects_to_hub() -> None:
    client = TestClient(create_app())
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (307, 302)
    assert resp.headers["location"] == "/pages/index.html"


def test_static_assets_served() -> None:
    client = TestClient(create_app())
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/js/app.js").status_code == 200
    assert client.get("/static/js/sse-client.js").status_code == 200
    assert client.get("/static/locales/ja.bundle.js").status_code == 200


def test_pages_served() -> None:
    client = TestClient(create_app())
    assert client.get("/pages/index.html").status_code == 200
    assert client.get("/pages/01_dashboard.html").status_code == 200
    body = client.get("/pages/01_dashboard.html").text
    assert "/static/css/style.css" in body
    assert "/static/js/sse-client.js" in body
