CREATE TABLE IF NOT EXISTS shards (
    id BIGSERIAL PRIMARY KEY,
    start_index BIGINT NOT NULL,
    end_index BIGINT NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    worker_id VARCHAR(64),
    error VARCHAR(256),
    claimed_at TIMESTAMPTZ,
    done_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_shards_status ON shards (status);

CREATE TABLE IF NOT EXISTS hits (
    id BIGSERIAL PRIMARY KEY,
    shard_id BIGINT REFERENCES shards(id),
    chain VARCHAR(8) NOT NULL,
    address VARCHAR(128) NOT NULL,
    seed VARCHAR(512) NOT NULL,
    balance BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_hits_address ON hits (address);