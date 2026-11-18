from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.models import Shard
from ports.shard_store import ShardStore

CLAIM_SQL = text(
    """
    UPDATE shards SET status = 'running', worker_id = :worker, claimed_at = now()
    WHERE id = (
        SELECT id FROM shards WHERE status = 'pending'
        ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1
    )
    RETURNING id, start_index, end_index
    """
)


class PgShardStore(ShardStore):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def claim(self, worker_id: str) -> Shard | None:
        async with self._sf() as session:
            async with session.begin():
                row = (await session.execute(CLAIM_SQL, {"worker": worker_id})).first()
            if row is None:
                return None
            return Shard(id=row.id, start_index=row.start_index, end_index=row.end_index)

    async def complete(self, shard_id: int) -> None:
        async with self._sf() as session:
            async with session.begin():
                await session.execute(
                    text("UPDATE shards SET status = 'done', done_at = now() WHERE id = :id"),
                    {"id": shard_id},
                )

    async def fail(self, shard_id: int, reason: str) -> None:
        async with self._sf() as session:
            async with session.begin():
                await session.execute(
                    text(
                        "UPDATE shards SET status = 'pending', worker_id = NULL, "
                        "error = :reason WHERE id = :id"
                    ),
                    {"id": shard_id, "reason": reason},
                )