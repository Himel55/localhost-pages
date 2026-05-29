import asyncio
import pytest
from localhost_pages.pubsub import PubSub


async def test_publish_to_subscriber():
    ps = PubSub()
    sub = ps.subscribe("alpha")
    try:
        await ps.publish("alpha")
        msg = await asyncio.wait_for(sub.get(), timeout=0.1)
        assert msg == "alpha"
    finally:
        ps.unsubscribe("alpha", sub)


async def test_publish_only_to_matching_topic():
    ps = PubSub()
    sub_a = ps.subscribe("alpha")
    sub_b = ps.subscribe("beta")
    try:
        await ps.publish("alpha")
        msg = await asyncio.wait_for(sub_a.get(), timeout=0.1)
        assert msg == "alpha"
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(sub_b.get(), timeout=0.05)
    finally:
        ps.unsubscribe("alpha", sub_a)
        ps.unsubscribe("beta", sub_b)


async def test_unsubscribe_removes_queue():
    ps = PubSub()
    sub = ps.subscribe("alpha")
    ps.unsubscribe("alpha", sub)
    await ps.publish("alpha")
