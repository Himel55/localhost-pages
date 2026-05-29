from pathlib import Path
from localhost_pages.bootstrap import seed_defaults, MARKER


def _make_docs(tmp_path: Path) -> Path:
    docs = tmp_path / "docs" / "explainer"
    docs.mkdir(parents=True)
    (docs / "index.html").write_text("<html></html>")
    return docs


def test_seeds_default_symlink_and_marker(tmp_path: Path, monkeypatch):
    docs = _make_docs(tmp_path)
    symlinks = tmp_path / "symlinks"
    symlinks.mkdir()
    monkeypatch.setattr(
        "localhost_pages.bootstrap.DEFAULT_APPS",
        {"technical-explanation": docs},
    )

    seed_defaults(symlinks)

    link = symlinks / "technical-explanation"
    assert link.is_symlink()
    assert link.resolve() == docs.resolve()
    assert (symlinks / MARKER).exists()


def test_noop_when_marker_present(tmp_path: Path, monkeypatch):
    docs = _make_docs(tmp_path)
    symlinks = tmp_path / "symlinks"
    symlinks.mkdir()
    (symlinks / MARKER).touch()  # already initialized
    monkeypatch.setattr(
        "localhost_pages.bootstrap.DEFAULT_APPS",
        {"technical-explanation": docs},
    )

    seed_defaults(symlinks)

    # deleted/never-created app stays absent
    assert not (symlinks / "technical-explanation").exists()


def test_skips_missing_target_but_still_marks(tmp_path: Path, monkeypatch):
    symlinks = tmp_path / "symlinks"
    symlinks.mkdir()
    monkeypatch.setattr(
        "localhost_pages.bootstrap.DEFAULT_APPS",
        {"technical-explanation": tmp_path / "docs" / "missing"},
    )

    seed_defaults(symlinks)

    assert not (symlinks / "technical-explanation").exists()
    assert (symlinks / MARKER).exists()  # marked, won't retry forever
