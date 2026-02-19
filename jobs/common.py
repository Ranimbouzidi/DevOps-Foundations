from __future__ import annotations

from uuid import uuid4

from core.models import METHOD_COST, JobRun, MethodUsed, QueueMessage, SnapshotRecord, normalized_hash, utc_now
from core.storage import LocalObjectStorage, LocalStructuredStorage


class JobContext:
    def __init__(self) -> None:
        self.blob = LocalObjectStorage()
        self.structured = LocalStructuredStorage()
        self.processed_keys: set[str] = set()

    def dedupe(self, msg: QueueMessage) -> bool:
        key = msg.idempotency_key(utc_now().strftime("%Y%m%d%H"))
        if key in self.processed_keys:
            return False
        self.processed_keys.add(key)
        return True

    def persist_snapshot(
        self,
        site: str,
        entity_id: str,
        content_type: str,
        raw_text: str,
        payload: dict,
        table: str,
    ) -> SnapshotRecord:
        sid = str(uuid4())
        uri = self.blob.put_text(site, f"{sid}.{content_type}.txt", raw_text)
        snapshot = SnapshotRecord(
            snapshot_id=sid,
            site=site,
            entity_id=entity_id,
            captured_at=utc_now(),
            content_hash=normalized_hash(raw_text),
            content_type=content_type,
            uri=uri,
            payload=payload,
        )
        self.structured.append_snapshot(table, snapshot)
        return snapshot

    def persist_job_run(
        self,
        msg: QueueMessage,
        method_used: MethodUsed,
        status: str,
        started_at,
        ended_at,
        bytes_in: int,
        items_out: int,
        snapshot_id: str | None,
        error_message: str | None = None,
    ) -> None:
        run = JobRun(
            idempotency_key=msg.idempotency_key(started_at.strftime("%Y%m%d%H")),
            job_type=msg.job_type,
            site=msg.site,
            target_id=msg.target_id,
            method_used=method_used,
            started_at=started_at,
            ended_at=ended_at,
            status=status,
            retry_count=msg.retry_count,
            bytes_in=bytes_in,
            items_out=items_out,
            snapshot_id=snapshot_id,
            cost_estimate_units=METHOD_COST[method_used],
            error_message=error_message,
        )
        self.structured.append_job_run(run)
