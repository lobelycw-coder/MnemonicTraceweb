from abc import ABC, abstractmethod

from domain.models import Shard


class ShardStore(ABC):
    @abstractmethod
    async def claim(self, worker_id: str) -> Shard | None: ...

    @abstractmethod
    async def complete(self, shard_id: int) -> None: ...

    @abstractmethod
    async def fail(self, shard_id: int, reason: str) -> None: ...
