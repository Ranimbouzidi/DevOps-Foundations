from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any


class JobType(str, Enum):
    DISCOVERY = "discovery"
    PAGE_SCRAPE = "page_scrape"
    PRODUCT_SCRAPE = "product_scrape"
    PDF_FETCH = "pdf_fetch"
    OCR = "ocr"
    DIFF = "diff"


class MethodUsed(str, Enum):
    HTML = "HTML"
    API = "API"
    HEADLESS = "HEADLESS"
    OCR = "OCR"


@dataclass(slots=True)
class QueueMessage:
    site: str
    job_type: JobType
    target_id: str
    target_url: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0

    def idempotency_key(self, bucket: str) -> str:
        return f"{self.site}:{self.job_type.value}:{self.target_id}:{bucket}"


@dataclass(slots=True)
class JobRun:
    idempotency_key: str
    job_type: JobType
    site: str
    target_id: str
    method_used: MethodUsed
    started_at: datetime
    ended_at: datetime
    status: str
    retry_count: int
    bytes_in: int
    items_out: int
    snapshot_id: str | None
    cost_estimate_units: float
    error_message: str | None = None

    @property
    def duration_ms(self) -> int:
        return int((self.ended_at - self.started_at).total_seconds() * 1000)


@dataclass(slots=True)
class SnapshotRecord:
    snapshot_id: str
    site: str
    entity_id: str
    captured_at: datetime
    content_hash: str
    content_type: str
    uri: str
    payload: dict[str, Any]


METHOD_COST = {
    MethodUsed.HTML: 1.0,
    MethodUsed.API: 1.2,
    MethodUsed.HEADLESS: 6.0,
    MethodUsed.OCR: 8.0,
}


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def normalized_hash(raw: str | bytes) -> str:
    if isinstance(raw, str):
        raw = " ".join(raw.split()).lower().encode("utf-8")
    return sha256(raw).hexdigest()
