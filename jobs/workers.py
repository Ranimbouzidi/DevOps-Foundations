from __future__ import annotations

import json
from uuid import uuid4

from core.models import JobType, MethodUsed, QueueMessage, utc_now
from core.queue import InMemoryQueueService
from jobs.common import JobContext


async def discovery_worker(msg: QueueMessage, ctx: JobContext, queue: InMemoryQueueService) -> None:
    started_at = utc_now()
    if not ctx.dedupe(msg):
        return
    fake_listing_urls = [f"{msg.site}/listing/{i}" for i in range(1, 3)]
    raw = json.dumps({"listings": fake_listing_urls})
    snapshot = ctx.persist_snapshot(msg.site, msg.target_id, "json", raw, {"listings": fake_listing_urls}, "product_snapshot")
    for url in fake_listing_urls:
        await queue.publish(
            JobType.PAGE_SCRAPE.value,
            QueueMessage(
                site=msg.site,
                job_type=JobType.PAGE_SCRAPE,
                target_id=str(uuid4()),
                target_url=url,
            ),
        )
    ended_at = utc_now()
    ctx.persist_job_run(msg, MethodUsed.HTML, "success", started_at, ended_at, len(raw), 2, snapshot.snapshot_id)


async def page_scrape_worker(msg: QueueMessage, ctx: JobContext, queue: InMemoryQueueService) -> None:
    started_at = utc_now()
    fake_products = [f"{msg.site}/product/{i}" for i in range(1, 4)]
    raw = json.dumps({"products": fake_products, "listing": msg.target_url})
    snapshot = ctx.persist_snapshot(msg.site, msg.target_id, "html", raw, {"products": fake_products}, "product_snapshot")
    for url in fake_products:
        await queue.publish(
            JobType.PRODUCT_SCRAPE.value,
            QueueMessage(
                site=msg.site,
                job_type=JobType.PRODUCT_SCRAPE,
                target_id=url.rsplit("/", 1)[-1],
                target_url=url,
            ),
        )
    ended_at = utc_now()
    ctx.persist_job_run(msg, MethodUsed.HTML, "success", started_at, ended_at, len(raw), 3, snapshot.snapshot_id)


async def product_scrape_worker(msg: QueueMessage, ctx: JobContext, queue: InMemoryQueueService) -> None:
    started_at = utc_now()
    product_data = {
        "sku": msg.target_id,
        "price": 4.5 + int(msg.target_id) if msg.target_id.isdigit() else 9.9,
        "promo": "-10%",
        "stock": "in_stock",
        "description": f"Product {msg.target_id} from {msg.site}",
        "images": [f"https://cdn.local/{msg.target_id}.jpg"],
        "category": "epicerie",
    }
    raw = json.dumps(product_data)
    method = MethodUsed.API if "api" in (msg.target_url or "") else MethodUsed.HTML
    snapshot = ctx.persist_snapshot(msg.site, msg.target_id, "json", raw, product_data, "product_snapshot")
    await queue.publish(
        JobType.DIFF.value,
        QueueMessage(site=msg.site, job_type=JobType.DIFF, target_id=msg.target_id, payload=product_data),
    )
    ended_at = utc_now()
    ctx.persist_job_run(msg, method, "success", started_at, ended_at, len(raw), 1, snapshot.snapshot_id)


async def pdf_fetch_worker(msg: QueueMessage, ctx: JobContext, queue: InMemoryQueueService) -> None:
    started_at = utc_now()
    urls = msg.payload.get("urls", [])
    for url in urls:
        pdf_text = f"PDF bytes for {url}"
        snap = ctx.persist_snapshot(msg.site, url, "pdf", pdf_text, {"source_url": url}, "pdf_snapshot")
        await queue.publish(
            JobType.OCR.value,
            QueueMessage(site=msg.site, job_type=JobType.OCR, target_id=snap.snapshot_id, payload={"uri": snap.uri}),
        )
    ended_at = utc_now()
    ctx.persist_job_run(msg, MethodUsed.HTML, "success", started_at, ended_at, len(urls), len(urls), None)


async def ocr_worker(msg: QueueMessage, ctx: JobContext) -> None:
    started_at = utc_now()
    text = f"OCR extracted text from {msg.payload.get('uri', 'unknown')}"
    snap = ctx.persist_snapshot(msg.site, msg.target_id, "txt", text, {"text": text}, "pdf_snapshot")
    ended_at = utc_now()
    ctx.persist_job_run(msg, MethodUsed.OCR, "success", started_at, ended_at, len(text), 1, snap.snapshot_id)


async def diff_worker(msg: QueueMessage, ctx: JobContext) -> None:
    started_at = utc_now()
    change = {
        "entity_id": msg.target_id,
        "site": msg.site,
        "change_type": "price_change",
        "new_value": msg.payload.get("price"),
    }
    raw = json.dumps(change)
    snap = ctx.persist_snapshot(msg.site, msg.target_id, "json", raw, change, "change_event")
    ended_at = utc_now()
    ctx.persist_job_run(msg, MethodUsed.HTML, "success", started_at, ended_at, len(raw), 1, snap.snapshot_id)
