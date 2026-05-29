from __future__ import annotations

import asyncio
from collections import defaultdict


class PubSub:
    """Async fan-out: publish a topic name; each subscriber to that topic
    gets the topic name dropped into its asyncio.Queue."""

    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)

    def subscribe(self, topic: str) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue()
        self._subs[topic].add(q)
        return q

    def unsubscribe(self, topic: str, q: asyncio.Queue[str]) -> None:
        self._subs[topic].discard(q)
        if not self._subs[topic]:
            self._subs.pop(topic, None)

    async def publish(self, topic: str) -> None:
        # Every queue is subscribed to exactly one topic, so any pending item
        # is necessarily this same topic. Skip the put when one is already
        # waiting — collapses bursts (and the dir+app double-publish of
        # INDEX_TOPIC) into a single wakeup per subscriber.
        for q in list(self._subs.get(topic, ())):
            if q.empty():
                await q.put(topic)
