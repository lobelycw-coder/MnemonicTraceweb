from abc import ABC, abstractmethod

from domain.models import Candidate


class BalanceSource(ABC):
    @property
    @abstractmethod
    def chain(self) -> str: ...

    @abstractmethod
    async def balance(self, candidate: Candidate) -> int:
        """Return balance in smallest unit. 0 = empty."""