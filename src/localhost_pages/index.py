from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .inject import reload_script_tag
from .registry import App
from .watcher import INDEX_TOPIC

_TEMPLATES = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES),
    autoescape=select_autoescape(["html"]),
)


def render_index(apps: list[App]) -> str:
    broken = sum(1 for a in apps if a.error)
    return _env.get_template("index.html").render(
        apps=apps, count=len(apps), broken=broken,
        reload_tag=reload_script_tag(INDEX_TOPIC),
    )
