from abc import ABC, abstractmethod
from typing import Sequence
from domain.models import Candidate

class Accelerator(ABC):
    """Pure contract. CPU implements it; CUDA optionally registers over it."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def derive_batch(self, seeds: Sequence[str], chains: Sequence[str]) -> list[Candidate]:
        """Derive addresses for a batch of seeds across the given chains."""