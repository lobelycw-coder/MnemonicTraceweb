import asyncio
from typing import Sequence

from domain.derivation import derive_addresses
from domain.models import Candidate
from ports.accelerator import Accelerator


class CpuBackend(Accelerator):
    def __init__(self, concurrency: int = 2) -> None:
        self._sem = asyncio.Semaphore(concurrency)

    @property
    def name(self) -> str:
        return "cpu"

    async def derive_batch(self, seeds: Sequence[str], chains: Sequence[str]) -> list[Candidate]:
        chain_tuple = tuple(chains)

        async def one(seed: str) -> tuple[Candidate, ...]:
            async with self._sem:
                return await asyncio.to_thread(derive_addresses, seed, chain_tuple)

        results = await asyncio.gather(*(one(s) for s in seeds))
        return [c for batch in results for c in batch]