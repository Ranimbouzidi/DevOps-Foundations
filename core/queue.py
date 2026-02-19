from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import timedelta
from typing import Awaitable, Callable

from core.models import QueueMessage


@dataclass(slots=True)
class RetryPolicy:
    max_retries: int = 5
    base_delay_seconds: float = 2
    jitter_seconds: float = 0.7

    def backoff_seconds(self, retry_count: int) -> float:
        exp = self.base_delay_seconds * (2 ** max(0, retry_count - 1))
        return exp + random.uniform(0, self.jitter_seconds)


class InMemoryQueueService:
    """Simple queue abstraction with DLQ and visibility timeout behavior."""

    def __init__(self, queue_names: list[str]) -> None:
        self.queues = {name: asyncio.Queue() for name in queue_names}
        self.dlq = {name: asyncio.Queue() for name in queue_names}

    async def publish(self, queue_name: str, msg: QueueMessage) -> None:
        await self.queues[queue_name].put(msg)

    async def consume_forever(
        self,
        queue_name: str,
        handler: Callable[[QueueMessage], Awaitable[None]],
        retry_policy: RetryPolicy,
        visibility_timeout: timedelta = timedelta(minutes=5),
    ) -> None:
        _ = visibility_timeout
        queue = self.queues[queue_name]
        while True:
            msg = await queue.get()
            try:
                await handler(msg)
            except Exception:
                msg.retry_count += 1
                if msg.retry_count > retry_policy.max_retries:
                    await self.dlq[queue_name].put(msg)
                else:
                    await asyncio.sleep(retry_policy.backoff_seconds(msg.retry_count))
                    await queue.put(msg)
            finally:
                queue.task_done()
