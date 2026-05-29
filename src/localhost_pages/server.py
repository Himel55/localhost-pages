from __future__ import annotations

import asyncio
import logging
import platform
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .bootstrap import seed_defaults
from .index import render_index
from .inject import inject_reload_script
from .logconfig import app_version, get_log_path
from .pubsub import PubSub
from .registry import scan
from .watcher import Watcher, INDEX_TOPIC

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SYMLINKS = REPO_ROOT / "symlinks"
STATIC_DIR = Path(__file__).parent / "static"
HTML_SUFFIXES = {".html", ".htm"}

# Caps on client-reported error fields so a noisy or hostile page can't bloat
# the log file or flood it with entries.
_MAX_MSG = 1_000
_MAX_STACK = 4_000
# Most of a diagnostics download is the log tail; bound it so the response
# stays a reasonable size to email/attach.
_MAX_LOG_CHARS = 200_000


def _is_within(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except (ValueError, OSError):
        return False


def create_app(symlinks_dir: Path = DEFAULT_SYMLINKS) -> FastAPI:
    pubsub = PubSub()
    watcher = Watcher(symlinks_dir, pubsub)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        symlinks_dir.mkdir(parents=True, exist_ok=True)
        seed_defaults(symlinks_dir)
        apps = scan(symlinks_dir)
        logger.info("apps registered: %d (%d broken)",
                    len(apps), sum(1 for a in apps if a.error))
        await watcher.start()
        try:
            yield
        finally:
            await watcher.stop()

    app = FastAPI(lifespan=lifespan)
    app.mount("/__static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            dur = (time.perf_counter() - start) * 1000
            # Full traceback for any unhandled error — these would otherwise be
            # invisible once the terminal scrolls away.
            logger.exception("unhandled error %s %s after %.0fms",
                             request.method, request.url.path, dur)
            raise
        dur = (time.perf_counter() - start) * 1000
        # Static asset hits (CSS/JS/1700+ icons) are noisy — keep them at DEBUG.
        level = logging.DEBUG if request.url.path.startswith("/__static") else logging.INFO
        logger.log(level, "%s %s -> %d (%.0fms)",
                   request.method, request.url.path, response.status_code, dur)
        return response

    @app.post("/__log", status_code=204)
    async def client_log(entry: dict = Body(default={})):
        """Receive a browser-side error (from lp-log.js) into the server log,
        so frontend and backend problems land in one file the user can send."""
        msg = str(entry.get("message", ""))[:_MAX_MSG]
        stack = str(entry.get("stack", ""))[:_MAX_STACK]
        logger.warning(
            "client error on %s: %s (%s:%s:%s) ua=%s%s",
            entry.get("page", "?"), msg,
            entry.get("source", ""), entry.get("line", ""), entry.get("column", ""),
            entry.get("userAgent", ""),
            ("\n" + stack) if stack else "",
        )

    @app.get("/__diagnostics", response_class=PlainTextResponse)
    async def diagnostics():
        """One-click bundle: environment + app inventory + the log tail, as a
        downloadable text file users can attach to a bug report."""
        apps = scan(symlinks_dir)
        out = [
            f"localhost-pages {app_version()} — diagnostics",
            f"generated: {datetime.now(timezone.utc).isoformat()}",
            f"python {platform.python_version()} on {platform.platform()}",
            f"symlinks dir: {symlinks_dir}",
            f"apps: {len(apps)} ({sum(1 for a in apps if a.error)} broken)",
        ]
        for a in apps:
            out.append(f"  - {a.name}: {('BROKEN: ' + (a.error or '')) if a.error else 'ok'}")
        path = get_log_path()
        out += ["", f"log file: {path}", "=" * 60]
        if path and path.exists():
            data = path.read_text(encoding="utf-8", errors="replace")
            if len(data) > _MAX_LOG_CHARS:
                data = "...[earlier log lines truncated]...\n" + data[-_MAX_LOG_CHARS:]
            out.append(data)
        else:
            out.append("(no log file on disk)")
        return PlainTextResponse(
            "\n".join(out),
            headers={"Content-Disposition":
                     'attachment; filename="localhost-pages-diagnostics.txt"'},
        )

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(render_index(scan(symlinks_dir)))

    @app.get("/__events")
    async def events(app: str = Query(default="")) -> StreamingResponse:
        topic = app or INDEX_TOPIC

        async def stream():
            q = pubsub.subscribe(topic)
            try:
                yield ": connected\n\n"
                while True:
                    try:
                        msg = await asyncio.wait_for(q.get(), timeout=15.0)
                        yield f"event: change\ndata: {msg}\n\n"
                    except asyncio.TimeoutError:
                        yield ": ping\n\n"
            finally:
                pubsub.unsubscribe(topic, q)

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.delete("/__apps/{name}", status_code=204)
    async def delete_app(name: str):
        if not name or name.startswith("__") or "/" in name or ".." in name:
            raise HTTPException(status_code=400, detail="invalid app name")
        path = symlinks_dir / name
        if not _is_within(path.parent, symlinks_dir):
            raise HTTPException(status_code=400, detail="path escapes symlinks dir")
        if path.is_symlink():
            try:
                path.unlink()
            except OSError as e:
                logger.error("failed to delete app %r at %s: %s", name, path, e)
                raise HTTPException(status_code=500, detail=str(e))
            logger.info("deleted app %r", name)
            return
        raise HTTPException(status_code=404, detail="not found")

    @app.delete("/__apps/{path:path}", status_code=400)
    async def delete_app_traversal(path: str):
        raise HTTPException(status_code=400, detail="invalid app name")

    @app.get("/{app_name}/{path:path}")
    async def serve_app(app_name: str, path: str):
        if app_name.startswith("__"):
            raise HTTPException(status_code=404)
        link = symlinks_dir / app_name
        if not link.is_symlink() and not link.exists():
            raise HTTPException(status_code=404)
        try:
            target = link.resolve(strict=True)
        except (FileNotFoundError, OSError):
            raise HTTPException(status_code=404)
        if not target.is_dir():
            raise HTTPException(status_code=404)

        rel = path or "index.html"
        if rel.endswith("/") or rel == "":
            rel = (rel + "index.html").lstrip("/")

        try:
            requested = (target / rel).resolve(strict=True)
        except (FileNotFoundError, OSError):
            raise HTTPException(status_code=404)
        if not _is_within(requested, target):
            raise HTTPException(status_code=404)
        if not requested.is_file():
            raise HTTPException(status_code=404)

        if requested.suffix.lower() in HTML_SUFFIXES:
            html = requested.read_text(encoding="utf-8", errors="replace")
            return HTMLResponse(inject_reload_script(html, app_name))
        return FileResponse(requested)

    return app
