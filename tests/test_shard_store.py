from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from adapters.store.pg_shard_store import PgShardStore
from domain.models import Shard


class AsyncContext:
    """Minimal async context manager used for mocked SQLAlchemy sessions."""

    def __init__(self, value=None):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_session_factory():
    session = MagicMock()
    session.execute = AsyncMock()
    session.begin = MagicMock(return_value=AsyncContext())

    def session_factory():
        return AsyncContext(session)

    return session_factory, session


@pytest.mark.asyncio
async def test_claim_returns_shard_when_pending_shard_exists():
    session_factory, session = make_session_factory()
    session.execute.return_value.first.return_value = SimpleNamespace(
        id=7,
        start_index=100,
        end_index=199,
    )

    store = PgShardStore(session_factory)

    result = await store.claim("worker-1")

    assert result == Shard(id=7, start_index=100, end_index=199)
    assert session.execute.await_count == 1
    call = session.execute.await_args
    assert call.args[1] == {"worker": "worker-1"}


@pytest.mark.asyncio
async def test_claim_returns_none_when_no_pending_shard_exists():
    session_factory, session = make_session_factory()
    session.execute.return_value.first.return_value = None

    store = PgShardStore(session_factory)

    result = await store.claim("worker-1")

    assert result is None


@pytest.mark.asyncio
async def test_complete_updates_shard_status():
    session_factory, session = make_session_factory()
    store = PgShardStore(session_factory)

    await store.complete(42)

    session.execute.assert_awaited_once()
    statement, parameters = session.execute.await_args.args
    assert "status = 'done'" in str(statement)
    assert parameters == {"id": 42}


@pytest.mark.asyncio
async def test_fail_resets_shard_status_and_sets_reason():
    session_factory, session = make_session_factory()
    store = PgShardStore(session_factory)

    await store.fail(42, "worker crashed")

    session.execute.assert_awaited_once()
    statement, parameters = session.execute.await_args.args
    assert "status = 'pending'" in str(statement)
    assert "worker_id = NULL" in str(statement)
    assert parameters == {"id": 42, "reason": "worker crashed"}
