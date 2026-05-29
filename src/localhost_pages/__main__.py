from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn

from .logconfig import log_startup_banner, setup_logging
from .server import create_app, DEFAULT_SYMLINKS

logger = logging.getLogger(__name__)


def main() -> None:
    # Logging is always on (rotating file + stderr). LOCALHOST_PAGES_LOG still
    # overrides the file location for users who want logs somewhere specific.
    setup_logging(os.environ.get("LOCALHOST_PAGES_LOG"))

    symlinks = Path(os.environ.get("LOCALHOST_PAGES_SYMLINKS", DEFAULT_SYMLINKS))
    host = os.environ.get("LOCALHOST_PAGES_HOST", "127.0.0.1")
    port = int(os.environ.get("LOCALHOST_PAGES_PORT", "8080"))

    log_startup_banner(logger, host=host, port=port, symlinks_dir=symlinks)

    app = create_app(symlinks_dir=symlinks)
    # access_log=False: our request-logging middleware already records every
    # request, so uvicorn's access log would just duplicate it.
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=False)


if __name__ == "__main__":
    main()
