from __future__ import annotations

import json
from pathlib import Path

from core.models import JobRun, SnapshotRecord


class LocalObjectStorage:
    def __init__(self, root: Path = Path("data/blob")) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put_text(self, site: str, name: str, content: str) -> str:
        folder = self.root / site
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_text(content, encoding="utf-8")
        return str(path)

    def put_bytes(self, site: str, name: str, content: bytes) -> str:
        folder = self.root / site
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_bytes(content)
        return str(path)


class LocalStructuredStorage:
    def __init__(self, root: Path = Path("data/structured")) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def append_job_run(self, job_run: JobRun) -> None:
        path = self.root / "job_run.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "idempotency_key": job_run.idempotency_key,
                        "job_type": job_run.job_type.value,
                        "site": job_run.site,
                        "target_id": job_run.target_id,
                        "method_used": job_run.method_used.value,
                        "started_at": job_run.started_at.isoformat(),
                        "ended_at": job_run.ended_at.isoformat(),
                        "duration_ms": job_run.duration_ms,
                        "status": job_run.status,
                        "retry_count": job_run.retry_count,
                        "bytes_in": job_run.bytes_in,
                        "items_out": job_run.items_out,
                        "snapshot_id": job_run.snapshot_id,
                        "cost_estimate_units": job_run.cost_estimate_units,
                        "error_message": job_run.error_message,
                    }
                )
                + "\n"
            )

    def append_snapshot(self, table: str, snapshot: SnapshotRecord) -> None:
        path = self.root / f"{table}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "snapshot_id": snapshot.snapshot_id,
                        "site": snapshot.site,
                        "entity_id": snapshot.entity_id,
                        "captured_at": snapshot.captured_at.isoformat(),
                        "content_hash": snapshot.content_hash,
                        "content_type": snapshot.content_type,
                        "uri": snapshot.uri,
                        "payload": snapshot.payload,
                    }
                )
                + "\n"
            )
