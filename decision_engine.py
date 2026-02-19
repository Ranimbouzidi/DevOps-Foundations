from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev

ALLOWED_FREQ_HOURS = [1, 2, 4, 8, 12, 24]
METHOD_WEIGHTS = {"HTML": 1.0, "API": 1.2, "HEADLESS": 6.0, "OCR": 8.0}
I_MIN = 1.0
K_SIGMA = 0.7


def load_job_runs(path: Path = Path("data/structured/job_run.jsonl")) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _bucket_changes(job_runs: list[dict]) -> dict[tuple[str, str], list[datetime]]:
    changes = defaultdict(list)
    for row in job_runs:
        if row["status"] != "success":
            continue
        key = (row["site"], row["job_type"])
        changes[key].append(datetime.fromisoformat(row["started_at"]))
    return changes


def _round_allowed(hours: float) -> int:
    return min(ALLOWED_FREQ_HOURS, key=lambda x: abs(x - hours))


def compute_scrape_plan(job_runs: list[dict]) -> dict:
    changes = _bucket_changes(job_runs)
    plan: dict[str, dict[str, str]] = defaultdict(dict)

    for (site, job_type), timestamps in changes.items():
        timestamps.sort()
        if len(timestamps) < 2:
            plan[site][job_type] = "24h"
            continue

        intervals = [
            (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600
            for i in range(1, len(timestamps))
        ]
        mu = mean(intervals)
        sigma = pstdev(intervals) if len(intervals) > 1 else 0
        i_raw = max(mu - K_SIGMA * sigma, I_MIN)

        method = next((r["method_used"] for r in job_runs if r["site"] == site and r["job_type"] == job_type), "HTML")
        weighted = i_raw * METHOD_WEIGHTS.get(method, 1.0)
        plan[site][job_type] = f"{_round_allowed(weighted)}h"

    return plan


def compute_worker_plan(scrape_plan: dict) -> dict:
    worker_plan = {
        "light_workers": {"min_replicas": 1, "max_replicas": 5, "targets": ["discovery", "page_scrape", "product_scrape", "pdf_fetch", "diff"]},
        "heavy_workers": {"min_replicas": 0, "max_replicas": 3, "targets": ["headless", "ocr"]},
    }

    freq_score = 0
    for jobs in scrape_plan.values():
        for freq in jobs.values():
            freq_score += 24 / int(freq.replace("h", ""))

    worker_plan["light_workers"]["max_replicas"] = max(3, min(20, math.ceil(freq_score / 8)))
    worker_plan["heavy_workers"]["max_replicas"] = max(2, min(10, math.ceil(freq_score / 15)))
    return worker_plan


def main() -> None:
    runs = load_job_runs()
    scrape_plan = compute_scrape_plan(runs)
    worker_plan = compute_worker_plan(scrape_plan)

    Path("scrape_plan.json").write_text(json.dumps(scrape_plan, indent=2), encoding="utf-8")
    Path("worker_plan.json").write_text(json.dumps(worker_plan, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
