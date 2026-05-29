import os
from pathlib import Path
from localhost_pages.registry import scan, App


def test_scan_empty(tmp_symlinks: Path):
    assert scan(tmp_symlinks) == []


def test_scan_valid_app_no_meta(tmp_symlinks: Path, make_app):
    make_app(tmp_symlinks, "alpha")
    apps = scan(tmp_symlinks)
    assert len(apps) == 1
    a = apps[0]
    assert a.name == "alpha"
    assert a.title == "alpha"
    assert a.description == ""
    assert a.icon == "box"
    assert a.error is None
    assert a.last_modified is not None


def test_scan_valid_app_with_meta(tmp_symlinks: Path, make_app):
    make_app(tmp_symlinks, "beta", meta={"title": "Beta!", "description": "d", "icon": "🚀"})
    a = scan(tmp_symlinks)[0]
    assert a.title == "Beta!"
    assert a.description == "d"
    assert a.icon == "🚀"


def test_scan_broken_symlink(tmp_symlinks: Path, make_app):
    make_app(tmp_symlinks, "broke", broken=True)
    a = scan(tmp_symlinks)[0]
    assert a.error is not None
    assert "broken" in a.error.lower() or "missing" in a.error.lower()


def test_scan_missing_index(tmp_symlinks: Path, make_app):
    make_app(tmp_symlinks, "noindex", missing_index=True)
    a = scan(tmp_symlinks)[0]
    assert a.error is not None
    assert "index.html" in a.error


def test_scan_malformed_meta(tmp_symlinks: Path, make_app):
    target = make_app(tmp_symlinks, "bad")
    (target / "meta.json").write_text("{not json")
    a = scan(tmp_symlinks)[0]
    assert a.error is None
    assert a.title == "bad"


def test_scan_sorted_alphabetically(tmp_symlinks: Path, make_app):
    make_app(tmp_symlinks, "zebra")
    make_app(tmp_symlinks, "apple")
    names = [a.name for a in scan(tmp_symlinks)]
    assert names == ["apple", "zebra"]


def test_app_has_accent_and_icon_svg(tmp_symlinks, make_app):
    make_app(tmp_symlinks, "scraper", meta={"icon": "box", "accent": "sage"})
    apps = scan(tmp_symlinks)
    app = apps[0]
    from localhost_pages.accents import NAMED_ACCENTS
    assert app.accent == NAMED_ACCENTS["sage"]
    assert app.icon_svg.startswith("<svg")


def test_missing_meta_uses_hash_accent(tmp_symlinks, make_app):
    make_app(tmp_symlinks, "hash-me")
    apps = scan(tmp_symlinks)
    assert apps[0].accent.startswith("#")
    assert len(apps[0].accent) == 7


def test_invalid_accent_falls_back_to_hash(tmp_symlinks, make_app):
    make_app(tmp_symlinks, "bad-accent", meta={"accent": "not-a-color"})
    apps = scan(tmp_symlinks)
    assert apps[0].accent.startswith("#")


def test_broken_app_has_red_accent(tmp_symlinks, make_app):
    make_app(tmp_symlinks, "broke", broken=True)
    apps = scan(tmp_symlinks)
    assert apps[0].error is not None
    assert apps[0].accent == "#d6928f"


def test_freshness_tracks_newest_file_not_just_index(tmp_symlinks, make_app):
    target = make_app(tmp_symlinks, "fresh")
    index = target / "index.html"
    other = target / "app.js"
    other.write_text("// code")
    old = 1_000_000_000  # 2001
    new = 2_000_000_000  # 2033
    os.utime(index, (old, old))
    os.utime(other, (new, new))
    a = scan(tmp_symlinks)[0]
    assert a.last_modified is not None
    assert a.last_modified.timestamp() == new


def test_whitespace_only_title_falls_back_to_name(tmp_symlinks, make_app):
    make_app(tmp_symlinks, "blanky", meta={"title": "   "})
    a = scan(tmp_symlinks)[0]
    assert a.title == "blanky"


def test_title_with_surrounding_whitespace_is_stripped(tmp_symlinks, make_app):
    make_app(tmp_symlinks, "padded", meta={"title": "  Padded App  "})
    a = scan(tmp_symlinks)[0]
    assert a.title == "Padded App"
