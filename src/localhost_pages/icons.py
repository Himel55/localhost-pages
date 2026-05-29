from __future__ import annotations

import logging
import re
from html import escape
from pathlib import Path

logger = logging.getLogger(__name__)

LUCIDE_DIR = Path(__file__).parent / "static" / "lucide"
_LUCIDE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_FALLBACK_NAME = "box"
_cache: dict[str, str] = {}


def _read_lucide(name: str) -> str | None:
    if name in _cache:
        return _cache[name]
    path = LUCIDE_DIR / f"{name}.svg"
    if not path.is_file():
        return None
    svg = path.read_text(encoding="utf-8").strip()
    _cache[name] = svg
    return svg


def resolve_icon(value: str | None) -> str:
    """Return inline-ready HTML for an app's icon.

    Branches (in order):
      1. None or empty           → bundled `box.svg`
      2. starts with `<svg`      → returned verbatim (operator-trusted)
      3. matches lucide name     → bundled svg, fallback to `box.svg` if missing
      4. anything else           → wrapped emoji span
    """
    if not value:
        value = _FALLBACK_NAME

    if value.startswith("<svg"):
        return value

    if _LUCIDE_NAME_RE.match(value):
        svg = _read_lucide(value)
        if svg is None:
            logger.warning("lucide icon %r not found, using %r", value, _FALLBACK_NAME)
            svg = _read_lucide(_FALLBACK_NAME)
            if svg is None:
                return '<span class="icon-emoji"></span>'
        return svg

    return f'<span class="icon-emoji">{escape(value)}</span>'
