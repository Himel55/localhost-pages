"""Central logging setup.

Logging is *always on* and writes to a rotating file at a platform-standard
location so that, when a user hits a bug, the logs already exist and can be
exported via the /__diagnostics endpoint — no env var or restart required.
The file path can still be overridden with LOCALHOST_PAGES_LOG.
"""
from __future__ import annotations

import logging
import os
import platform
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import __version__

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_MAX_BYTES = 1_000_000  # 1 MB per file
_BACKUPS = 5            # keep ~5 MB of history

# Resolved at setup_logging() time so the /__diagnostics endpoint and the
# startup banner can report exactly where logs are written.
_log_path: Path | None = None


def app_version() -> str:
    # Read straight from the package __version__ so it's correct regardless of
    # whether the package is pip-installed (no importlib.metadata dependency).
    return __version__


def default_log_path() -> Path:
    """Platform-standard log location."""
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Logs"
    elif system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "localhost-pages" / "Logs"
    else:  # Linux / other POSIX
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "localhost-pages"
    return base / "localhost-pages.log"


def setup_logging(log_file: str | os.PathLike[str] | None = None) -> Path:
    """Configure the root logger with a rotating file handler + stderr.

    Returns the resolved log file path. Idempotent: clears any handlers it
    finds first so repeated calls (e.g. in tests) don't duplicate output.
    """
    global _log_path
    path = Path(log_file) if log_file else default_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    fmt = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        path, maxBytes=_MAX_BYTES, backupCount=_BACKUPS, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Mirror to stderr only when interactive. Under a daemon (launchd/systemd)
    # stderr is redirected to a file, so a stderr handler would duplicate every
    # line into that file alongside the rotating handler — the file handler
    # alone is the canonical sink there.
    if sys.stderr is not None and sys.stderr.isatty():
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(fmt)
        root.addHandler(stderr_handler)

    _log_path = path
    return path


def get_log_path() -> Path | None:
    """The active log file path, or None if setup_logging() hasn't run."""
    return _log_path


def log_startup_banner(logger: logging.Logger, *, host, port, symlinks_dir, app_count=None) -> None:
    """Log environment/config — the first thing you want when triaging a report."""
    logger.info("=" * 60)
    logger.info("localhost-pages %s starting", app_version())
    logger.info("python %s on %s %s", platform.python_version(), platform.system(), platform.release())
    logger.info("serving http://%s:%s", host, port)
    logger.info("symlinks dir: %s", symlinks_dir)
    logger.info("log file: %s", _log_path)
    if app_count is not None:
        logger.info("apps registered: %d", app_count)
    logger.info("=" * 60)
