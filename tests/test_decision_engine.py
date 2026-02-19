from decision_engine import compute_scrape_plan, compute_worker_plan


def test_compute_scrape_plan_generates_allowed_frequencies() -> None:
    runs = [
        {
            "site": "aziza",
            "job_type": "product_scrape",
            "method_used": "HTML",
            "status": "success",
            "started_at": "2026-01-01T00:00:00+00:00",
        },
        {
            "site": "aziza",
            "job_type": "product_scrape",
            "method_used": "HTML",
            "status": "success",
            "started_at": "2026-01-01T04:00:00+00:00",
        },
    ]
    plan = compute_scrape_plan(runs)
    assert plan["aziza"]["product_scrape"] in {"1h", "2h", "4h", "8h", "12h", "24h"}


def test_compute_worker_plan_shapes_ranges() -> None:
    scrape_plan = {"aziza": {"product_scrape": "4h", "discovery": "2h"}}
    worker_plan = compute_worker_plan(scrape_plan)
    assert worker_plan["light_workers"]["max_replicas"] >= worker_plan["light_workers"]["min_replicas"]
    assert worker_plan["heavy_workers"]["max_replicas"] >= worker_plan["heavy_workers"]["min_replicas"]
