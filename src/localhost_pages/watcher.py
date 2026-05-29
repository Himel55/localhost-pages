from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from watchfiles import awatch

from .pubsub import PubSub
from .registry import scan

logger = logging.getLogger(__name__)
INDEX_TOPIC = "__index"


class Watcher:
    """Watches the symlinks directory and the resolved target of each link.
    On any change, publishes the affected app name (or INDEX_TOPIC) onto the
    given PubSub. Debounces bursts of events.

    Resilience: each watch coroutine wraps its awatch() loop in a retry
    loop with exponential backoff so an unexpected exception (FSEvents
    glitch, transient OSError) doesn't permanently kill the watch. A
    periodic reaper task also re-syncs every REAP_INTERVAL_S seconds so
    any task that did exit gets recreated even without an external
    trigger."""

    REAP_INTERVAL_S = 60.0
    BACKOFF_INITIAL_S = 1.0
    BACKOFF_MAX_S = 30.0

    def __init__(self, symlinks_dir: Path, pubsub: PubSub, debounce_ms: int = 300) -> None:
        self.symlinks_dir = symlinks_dir
        self.pubsub = pubsub
        self.debounce_ms = debounce_ms
        self._tasks: list[asyncio.Task] = []
        self._stop = asyncio.Event()
        self._app_tasks: dict[str, asyncio.Task] = {}

    async def start(self) -> None:
        self._tasks.append(asyncio.create_task(self._watch_symlinks_dir()))
        self._tasks.append(asyncio.create_task(self._reaper()))
        await self._sync_app_watches()

    async def stop(self) -> None:
        self._stop.set()
        for t in self._tasks:
            t.cancel()
        for t in self._app_tasks.values():
            t.cancel()
        await asyncio.gather(*self._tasks, *self._app_tasks.values(), return_exceptions=True)
        self._tasks.clear()
        self._app_tasks.clear()

    async def _watch_symlinks_dir(self) -> None:
        backoff = self.BACKOFF_INITIAL_S
        while not self._stop.is_set():
            try:
                async for _ in awatch(self.symlinks_dir, stop_event=self._stop,
                                      debounce=self.debounce_ms, recursive=False):
                    await self.pubsub.publish(INDEX_TOPIC)
                    await self._sync_app_watches()
                    backoff = self.BACKOFF_INITIAL_S
                return  # awatch exited cleanly because _stop was set
            except Exception:
                logger.exception("symlinks dir watch crashed; restarting in %.1fs", backoff)
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=backoff)
                    return  # asked to stop while sleeping
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, self.BACKOFF_MAX_S)

    async def _sync_app_watches(self) -> None:
        apps = scan(self.symlinks_dir)
        wanted = {a.name: a for a in apps if a.target is not None and a.error is None}

        for name in list(self._app_tasks):
            if name not in wanted:
                self._app_tasks[name].cancel()
                del self._app_tasks[name]

        for name, app in wanted.items():
            existing = self._app_tasks.get(name)
            if existing and not existing.done():
                continue
            self._app_tasks[name] = asyncio.create_task(
                self._watch_app(name, app.target)
            )

    async def _watch_app(self, name: str, target: Path) -> None:
        backoff = self.BACKOFF_INITIAL_S
        while not self._stop.is_set():
            try:
                async for _ in awatch(target, stop_event=self._stop,
                                      debounce=self.debounce_ms, recursive=True):
                    await self.pubsub.publish(name)
                    # Also reload the index so the per-row "NEW" indicator
                    # picks up the freshness change.
                    await self.pubsub.publish(INDEX_TOPIC)
                    backoff = self.BACKOFF_INITIAL_S
                return
            except FileNotFoundError:
                # Target went away (symlink target deleted). Don't retry —
                # the symlinks-dir watcher will notice and call
                # _sync_app_watches, which drops us from the dict.
                logger.info("app %s target vanished; exiting watch", name)
                return
            except Exception:
                logger.exception("app %s watch crashed; restarting in %.1fs", name, backoff)
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=backoff)
                    return
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, self.BACKOFF_MAX_S)

    async def _reaper(self) -> None:
        """Periodically resync app watches. Cleans up any per-app task that
        exited (crash or clean return) and recreates watches for newly
        wanted apps that are missing. This is the safety net against silent
        watcher death."""
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.REAP_INTERVAL_S)
                return
            except asyncio.TimeoutError:
                pass
            dead = [n for n, t in self._app_tasks.items() if t.done()]
            for n in dead:
                logger.warning("reaper: app watch %s was dead, recreating", n)
                del self._app_tasks[n]
            try:
                await self._sync_app_watches()
            except Exception:
                logger.exception("reaper: _sync_app_watches failed")
