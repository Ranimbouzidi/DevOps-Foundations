from __future__ import annotations

from datetime import datetime, timezone

from core.models import JobType, QueueMessage
from core.queue import InMemoryQueueService


DEFAULT_FREQUENCIES = {
    JobType.DISCOVERY: "2h",
    JobType.PAGE_SCRAPE: "4h",
    JobType.PRODUCT_SCRAPE: "4h",
    JobType.PDF_FETCH: "24h",
}


class Scheduler:
    def __init__(self, queue_service: InMemoryQueueService) -> None:
        self.queue_service = queue_service

    async def seed_initial_jobs(self, site_configs: list[dict]) -> None:
        now_bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        for site in site_configs:
            site_name = site["site"]
            await self.queue_service.publish(
                JobType.DISCOVERY.value,
                QueueMessage(
                    site=site_name,
                    job_type=JobType.DISCOVERY,
                    target_id=f"{site_name}-root-{now_bucket}",
                    target_url=site["base_url"],
                ),
            )
            if site.get("pdf_catalog_urls"):
                await self.queue_service.publish(
                    JobType.PDF_FETCH.value,
                    QueueMessage(
                        site=site_name,
                        job_type=JobType.PDF_FETCH,
                        target_id=f"{site_name}-pdf-{now_bucket}",
                        payload={"urls": site["pdf_catalog_urls"]},
                    ),
                )
