from datetime import datetime, timezone
from localhost_pages.index import render_index
from localhost_pages.registry import App


def _app(name="alpha", error=None):
    return App(name=name, target=None, title=name.title(), description="desc",
               icon="🚀", icon_svg='<span class="icon-emoji">🚀</span>',
               accent="#7fb8ff",
               last_modified=datetime(2026, 5, 12, tzinfo=timezone.utc),
               error=error)


def test_render_lists_apps():
    html = render_index([_app("alpha"), _app("beta")])
    assert "alpha" in html
    assert "beta" in html
    assert 'href="/alpha/"' in html
    assert 'href="/beta/"' in html


def test_render_shows_error_for_broken():
    html = render_index([_app("oops", error="broken symlink")])
    assert "broken symlink" in html


def test_render_empty():
    html = render_index([])
    assert "no apps" in html.lower()


def test_render_includes_index_reload_script():
    html = render_index([])
    assert 'data-app="__index"' in html


def test_row_has_data_mtime():
    from localhost_pages.index import render_index
    from localhost_pages.registry import App
    from datetime import datetime as _dt, timezone as _tz
    ts = _dt(2026, 5, 14, 12, 0, 0, tzinfo=_tz.utc)
    app = App(name="x", target=None, title="x", description="d", icon="box",
              icon_svg="<svg></svg>", accent="#a8c8a3",
              last_modified=ts, error=None)
    html = render_index([app])
    assert 'data-mtime="2026-05-14T12:00:00+00:00"' in html


def _fake_app(**kw):
    defaults = dict(
        name="x", target=None, title="x", description="d", icon="box",
        icon_svg="<svg></svg>", accent="#7fffaf",
        last_modified=datetime.now(tz=timezone.utc), error=None,
    )
    defaults.update(kw)
    return App(**defaults)


def test_row_has_data_name_and_accent_var():
    html = render_index([_fake_app(name="my-app", accent="#7fffaf")])
    assert 'data-name="my-app"' in html
    assert "--accent: #7fffaf" in html


def test_row_has_delete_button_with_aria_label():
    html = render_index([_fake_app(name="zap")])
    assert 'aria-label="Delete zap"' in html


def test_header_shows_count_and_broken():
    apps = [_fake_app(name="ok"), _fake_app(name="bad", error="missing index.html", accent="#ff5e5e")]
    html = render_index(apps)
    assert "[2 APPS · 1 BROKEN]" in html


def test_brutalist_brand_present():
    html = render_index([])
    assert "LOCALHOST/" in html
    assert "[NO APPS]" in html


def test_app_name_with_special_chars_is_url_encoded_in_href():
    html = render_index([_fake_app(name="my#app")])
    assert 'href="/my%23app/"' in html
    # data-name keeps the raw (HTML-escaped) value for the JS that rebuilds URLs.
    assert 'data-name="my#app"' in html


def test_index_has_viewport_meta():
    html = render_index([])
    assert 'name="viewport"' in html
