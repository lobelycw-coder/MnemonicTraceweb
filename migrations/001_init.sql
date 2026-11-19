-- Initial MnemonicTrace database schema

CREATE TABLE IF NOT EXISTS shards (
    id BIGINT PRIMARY KEY,
    start_index BIGINT NOT NULL,
    end_index BIGINT NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    worker_id VARCHAR(64),
    error VARCHAR(256),
    claimed_at TIMESTAMPTZ,
    done_at TIMESTAMPTZ,

    CONSTRAINT shards_status_check
        CHECK (status IN ('pending', 'running', 'done', 'failed'))
);

CREATE INDEX IF NOT EXISTS ix_shards_status ON shards (status);

CREATE TABLE IF NOT EXISTS hits (
    id BIGINT PRIMARY KEY,
    shard_id BIGINT NOT NULL REFERENCES shards(id) ON DELETE CASCADE,
    chain VARCHAR(8) NOT NULL,
    address VARCHAR(128) NOT NULL,
    seed VARCHAR(512) NOT NULL,
    balance BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_hits_shard_id ON hits (shard_id);
CREATE INDEX IF NOT EXISTS ix_hits_address ON hits (address);
