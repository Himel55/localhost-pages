import os
from pathlib import Path
import pytest


@pytest.fixture
def tmp_symlinks(tmp_path: Path) -> Path:
    """A fresh symlinks directory for tests."""
    d = tmp_path / "symlinks"
    d.mkdir()
    return d


@pytest.fixture
def make_app(tmp_path: Path):
    """Factory: creates an app dir with index.html and optional meta.json,
    then symlinks it into the given symlinks directory under `name`."""
    counter = {"i": 0}

    def _make(symlinks_dir: Path, name: str, html: str = "<html><body>hi</body></html>",
              meta: dict | None = None, missing_index: bool = False, broken: bool = False) -> Path:
        counter["i"] += 1
        target = tmp_path / f"app{counter['i']}"
        target.mkdir()
        if not missing_index:
            (target / "index.html").write_text(html)
        if meta is not None:
            import json
            (target / "meta.json").write_text(json.dumps(meta))
        link = symlinks_dir / name
        if broken:
            os.symlink(tmp_path / "does-not-exist", link)
        else:
            os.symlink(target, link)
        return target

    return _make
