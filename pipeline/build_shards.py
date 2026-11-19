import asyncio
import sys

from sqlalchemy import text

from adapters.db.session import session_factory

SHARD_SIZE = 500


async def build(total: int) -> None:
    async with session_factory() as session:
        async with session.begin():
            for start in range(0, total, SHARD_SIZE):
                end = min(start + SHARD_SIZE, total)
                await session.execute(
                    text("INSERT INTO shards (start_index, end_index, status) VALUES (:s, :e, 'pending')"),
                    {"s": start, "e": end},
                )


if __name__ == "__main__":
    asyncio.run(build(int(sys.argv[1]) if len(sys.argv) > 1 else 100_000))