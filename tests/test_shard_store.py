import os

import pytest
from sqlalchemy import text

from adapters.db.session import session_factory
from adapters.store.pg_shard_store import PgShardStore

pytestmark = pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="needs db")


@pytest.fixture
async def store():
    async with session_factory() as s:
        async with s.begin():
            await s.execute(text("TRUNCATE shards, hits RESTART IDENTITY"))
            await s.execute(text("INSERT INTO shards (start_index, end_index) VALUES (0, 10)"))
    yield PgShardStore(session_factory)
    async with session_factory() as s:
        async with s.begin():
            await s.execute(text("TRUNCATE shards, hits RESTART IDENTITY"))


async def test_claim_and_complete(store):
    shard = await store.claim("w1")
    assert shard is not None
    await store.complete(shard.id)
    assert await store.claim("w2") is None


async def test_fail_returns_to_pending(store):
    shard = await store.claim("w1")
    await store.fail(shard.id, "boom")
    again = await store.claim("w2")
    assert again.id == shard.id