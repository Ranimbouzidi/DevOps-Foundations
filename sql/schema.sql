CREATE TABLE IF NOT EXISTS product_snapshot (
    snapshot_id UUID PRIMARY KEY,
    site TEXT NOT NULL,
    product_id TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    content_hash TEXT NOT NULL,
    raw_uri TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS pdf_snapshot (
    snapshot_id UUID PRIMARY KEY,
    site TEXT NOT NULL,
    source_id TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    content_hash TEXT NOT NULL,
    raw_uri TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS change_event (
    event_id UUID PRIMARY KEY,
    site TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    previous_snapshot_id UUID,
    current_snapshot_id UUID,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_run (
    run_id BIGSERIAL PRIMARY KEY,
    idempotency_key TEXT UNIQUE NOT NULL,
    job_type TEXT NOT NULL,
    site TEXT NOT NULL,
    target_id TEXT NOT NULL,
    method_used TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ NOT NULL,
    duration_ms INT NOT NULL,
    status TEXT NOT NULL,
    retry_count INT NOT NULL,
    bytes_in BIGINT NOT NULL,
    items_out INT NOT NULL,
    snapshot_id UUID,
    cost_estimate_units NUMERIC(10,2) NOT NULL,
    error_message TEXT
);
