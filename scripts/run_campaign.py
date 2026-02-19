from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import load_site_configs
from core.models import JobType
from core.queue import InMemoryQueueService, RetryPolicy
from core.scheduler import Scheduler
from jobs.common import JobContext
from jobs.workers import (
    diff_worker,
    discovery_worker,
    ocr_worker,
    page_scrape_worker,
    pdf_fetch_worker,
    product_scrape_worker,
)


async def run_simulation(cycles: int = 1) -> None:
    queues = [j.value for j in JobType]
    queue = InMemoryQueueService(queues)
    scheduler = Scheduler(queue)
    ctx = JobContext()
    configs = load_site_configs()
    await scheduler.seed_initial_jobs(configs)

    retry = RetryPolicy()

    async def consume_once(queue_name: str, limit: int = 50):
        consumed = 0
        while consumed < limit and not queue.queues[queue_name].empty():
            msg = await queue.queues[queue_name].get()
            try:
                if queue_name == JobType.DISCOVERY.value:
                    await discovery_worker(msg, ctx, queue)
                elif queue_name == JobType.PAGE_SCRAPE.value:
                    await page_scrape_worker(msg, ctx, queue)
                elif queue_name == JobType.PRODUCT_SCRAPE.value:
                    await product_scrape_worker(msg, ctx, queue)
                elif queue_name == JobType.PDF_FETCH.value:
                    await pdf_fetch_worker(msg, ctx, queue)
                elif queue_name == JobType.OCR.value:
                    await ocr_worker(msg, ctx)
                elif queue_name == JobType.DIFF.value:
                    await diff_worker(msg, ctx)
            except Exception:
                msg.retry_count += 1
                if msg.retry_count <= retry.max_retries:
                    await queue.publish(queue_name, msg)
                else:
                    await queue.dlq[queue_name].put(msg)
            finally:
                queue.queues[queue_name].task_done()
            consumed += 1

    for _ in range(cycles):
        for q in queues:
            await consume_once(q)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=3)
    args = parser.parse_args()
    asyncio.run(run_simulation(cycles=args.cycles))
