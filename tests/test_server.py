from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from localhost_pages.server import create_app


@pytest.fixture
def client(tmp_symlinks: Path):
    app = create_app(symlinks_dir=tmp_symlinks)
    with TestClient(app) as c:
        yield c


def test_index_lists_apps(client, tmp_symlinks, make_app):
    make_app(tmp_symlinks, "alpha", meta={"title": "Alpha App"})
    r = client.get("/")
    assert r.status_code == 200
    assert "alpha" in r.text
    assert 'href="/alpha/"' in r.text


def test_serves_app_index_with_injection(client, tmp_symlinks, make_app):
    make_app(tmp_symlinks, "alpha", html="<html><body>hello</body></html>")
    r = client.get("/alpha/")
    assert r.status_code == 200
    assert "hello" in r.text
    assert "data-localhost-pages-reload" in r.text
    assert 'data-app="alpha"' in r.text


def test_serves_explicit_index_html(client, tmp_symlinks, make_app):
    make_app(tmp_symlinks, "alpha", html="<html><body>explicit</body></html>")
    r = client.get("/alpha/index.html")
    assert r.status_code == 200
    assert "explicit" in r.text


def test_serves_static_asset_unmodified(client, tmp_symlinks, make_app):
    target = make_app(tmp_symlinks, "alpha")
    (target / "data.json").write_text('{"x": 1}')
    r = client.get("/alpha/data.json")
    assert r.status_code == 200
    assert r.json() == {"x": 1}


def test_path_traversal_rejected(client, tmp_symlinks, make_app):
    make_app(tmp_symlinks, "alpha")
    r = client.get("/alpha/../../etc/passwd")
    assert r.status_code in (400, 404)


def test_unknown_app_404(client):
    r = client.get("/nope/")
    assert r.status_code == 404


def test_static_assets_served(client):
    r = client.get("/__static/reload.js")
    assert r.status_code == 200
    assert "EventSource" in r.text


# SSE endpoint wiring is exercised by the smoke test in scripts/ — TestClient's
# sync stream API hangs on infinite generators. The pubsub fan-out and watcher
# integration are covered by test_pubsub and test_watcher.


def test_delete_unlinks_symlink(tmp_symlinks, make_app):
    make_app(tmp_symlinks, "doomed")
    app = create_app(symlinks_dir=tmp_symlinks)
    with TestClient(app) as client:
        assert (tmp_symlinks / "doomed").exists()
        r = client.delete("/__apps/doomed")
        assert r.status_code == 204
        assert not (tmp_symlinks / "doomed").exists()


def test_delete_refuses_real_directory(tmp_symlinks):
    real = tmp_symlinks / "real-dir"
    real.mkdir()
    (real / "index.html").write_text("<h1>hi</h1>")
    app = create_app(symlinks_dir=tmp_symlinks)
    with TestClient(app) as client:
        r = client.delete("/__apps/real-dir")
        assert r.status_code == 404
        assert real.exists()


def test_delete_404_when_missing(tmp_symlinks):
    app = create_app(symlinks_dir=tmp_symlinks)
    with TestClient(app) as client:
        r = client.delete("/__apps/nothing-here")
        assert r.status_code == 404


def test_delete_400_on_reserved_name(tmp_symlinks):
    app = create_app(symlinks_dir=tmp_symlinks)
    with TestClient(app) as client:
        r = client.delete("/__apps/__events")
        assert r.status_code == 400


def test_delete_400_on_traversal(tmp_symlinks):
    app = create_app(symlinks_dir=tmp_symlinks)
    with TestClient(app) as client:
        r = client.delete("/__apps/..%2Fetc")
        assert r.status_code == 400


def test_client_log_accepts_browser_error(client):
    r = client.post("/__log", json={
        "message": "boom", "page": "/alpha/", "stack": "Error: boom\n  at x",
    })
    assert r.status_code == 204


def test_diagnostics_bundle(client, tmp_symlinks, make_app):
    make_app(tmp_symlinks, "alpha", meta={"title": "Alpha App"})
    r = client.get("/__diagnostics")
    assert r.status_code == 200
    assert "localhost-pages" in r.text
    assert "alpha" in r.text
    assert "attachment" in r.headers["content-disposition"]


def test_app_pages_get_reload_but_not_error_capture(client, tmp_symlinks, make_app):
    # Served user apps get live-reload, but NOT the error-capture script —
    # their own runtime errors are not localhost-pages bugs.
    make_app(tmp_symlinks, "alpha", html="<html><body>hi</body></html>")
    r = client.get("/alpha/")
    assert "data-localhost-pages-reload" in r.text
    assert "lp-log.js" not in r.text


def test_dashboard_loads_error_capture(client):
    r = client.get("/")
    assert "lp-log.js" in r.text


def test_lifespan_seeds_default_app(tmp_path, monkeypatch):
    docs = tmp_path / "docs" / "explainer"
    docs.mkdir(parents=True)
    (docs / "index.html").write_text("<html>explainer</html>")
    monkeypatch.setattr(
        "localhost_pages.bootstrap.DEFAULT_APPS",
        {"technical-explanation": docs},
    )

    symlinks = tmp_path / "symlinks"
    app = create_app(symlinks_dir=symlinks)
    with TestClient(app):  # triggers lifespan startup
        assert (symlinks / "technical-explanation").is_symlink()
