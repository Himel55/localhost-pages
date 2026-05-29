from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .accents import resolve_accent
from .icons import resolve_icon

logger = logging.getLogger(__name__)

DEFAULT_ICON = "box"  # Lucide name


@dataclass(frozen=True)
class App:
    name: str
    target: Path | None
    title: str
    description: str
    icon: str
    icon_svg: str
    accent: str
    last_modified: datetime | None
    error: str | None

    @property
    def mtime_iso(self) -> str:
        return self.last_modified.isoformat() if self.last_modified else ""


def scan(symlinks_dir: Path) -> list[App]:
    try:
        entries = sorted(symlinks_dir.iterdir(), key=lambda p: p.name)
    except FileNotFoundError:
        return []
    return [_load(e) for e in entries if not e.name.startswith(".")]


def _broken(name: str, error: str) -> App:
    return App(
        name=name, target=None, title=name, description="",
        icon=DEFAULT_ICON, icon_svg=resolve_icon(DEFAULT_ICON),
        accent="#d6928f",  # broken rows always dusty rose
        last_modified=None, error=error,
    )


def _load(link: Path) -> App:
    name = link.name
    try:
        target = link.resolve(strict=True)
    except (FileNotFoundError, OSError) as e:
        return _broken(name, f"broken symlink: {e}")
    if not target.is_dir():
        return _broken(name, "symlink target is not a directory")
    index = target / "index.html"
    if not index.exists():
        return _broken(name, "missing index.html")
    meta = _load_meta(target / "meta.json", name)
    last_modified = datetime.fromtimestamp(_newest_mtime(target, index), tz=timezone.utc)
    return App(
        name=name, target=target,
        title=meta["title"], description=meta["description"],
        icon=meta["icon"], icon_svg=resolve_icon(meta["icon"]),
        accent=resolve_accent(meta.get("accent"), name),
        last_modified=last_modified, error=None,
    )


def _newest_mtime(target: Path, index: Path) -> float:
    """Freshness of an app = the newest mtime among all of its files, not
    just index.html. Editing style.css / app.js must also bump the row's
    "NEW" indicator. Falls back to index.html's mtime if the tree can't be
    walked (permission error, etc.)."""
    try:
        return max(
            (p.stat().st_mtime for p in target.rglob("*") if p.is_file()),
            default=index.stat().st_mtime,
        )
    except OSError as e:
        # The only fully-silent fallback in the backend: surfaces nowhere in
        # the UI or /__diagnostics. Log at DEBUG so a stale "NEW" badge report
        # can be traced to a permission/IO error without adding INFO noise.
        logger.debug("could not walk %s for mtime, using index.html: %s", target, e)
        return index.stat().st_mtime


def _load_meta(path: Path, name: str) -> dict:
    defaults = {"title": name, "description": "", "icon": DEFAULT_ICON, "accent": None}
    if not path.exists():
        return defaults
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("malformed meta.json at %s: %s", path, e)
        return defaults
    if not isinstance(data, dict):
        logger.warning("meta.json at %s is not an object", path)
        return defaults
    out = dict(defaults)
    for k in ("title", "description", "icon", "accent"):
        v = data.get(k)
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()
    return out
