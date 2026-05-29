import asyncio
from pathlib import Path
from localhost_pages.pubsub import PubSub
from localhost_pages.watcher import Watcher

INDEX_TOPIC = "__index"


async def test_file_change_emits_app_topic(tmp_symlinks: Path, make_app):
    target = make_app(tmp_symlinks, "alpha")
    ps = PubSub()
    sub = ps.subscribe("alpha")
    w = Watcher(tmp_symlinks, ps, debounce_ms=50)
    await w.start()
    try:
        await asyncio.sleep(0.3)
        (target / "index.html").write_text("<html><body>changed</body></html>")
        msg = await asyncio.wait_for(sub.get(), timeout=3.0)
        assert msg == "alpha"
    finally:
        await w.stop()


async def test_symlinks_dir_change_emits_index_topic(tmp_symlinks: Path, make_app):
    ps = PubSub()
    sub = ps.subscribe(INDEX_TOPIC)
    w = Watcher(tmp_symlinks, ps, debounce_ms=50)
    await w.start()
    try:
        await asyncio.sleep(0.3)
        make_app(tmp_symlinks, "newone")
        msg = await asyncio.wait_for(sub.get(), timeout=3.0)
        assert msg == INDEX_TOPIC
    finally:
        await w.stop()
