from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKER = ".initialized"

# slug -> bundled docs directory
DEFAULT_APPS = {"technical-explanation": REPO_ROOT / "docs" / "explainer"}


def seed_defaults(symlinks_dir: Path) -> None:
    """Register bundled default apps once, on first run.

    Writes a marker so seeding never repeats — a default the user later
    deletes stays gone.
    """
    marker = symlinks_dir / MARKER
    if marker.exists():
        return
    for slug, target in DEFAULT_APPS.items():
        link = symlinks_dir / slug
        if link.exists():
            continue
        if not target.exists():
            logger.warning("default app %r target missing: %s", slug, target)
            continue
        link.symlink_to(target)
        logger.info("registered default app %r -> %s", slug, target)
    marker.touch()
