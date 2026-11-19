import asyncio
import logging
import os

from workers.shard_runner import ShardRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")


async def main() -> None:
    n = int(os.environ.get("WORKER_COUNT", "2"))
    await asyncio.gather(*(ShardRunner().run() for _ in range(n)))


if __name__ == "__main__":
    asyncio.run(main())