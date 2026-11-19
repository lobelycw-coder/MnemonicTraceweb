import asyncio

import httpx

from domain.models import Candidate
from ports.balance_source import BalanceSource

BASE = "https://blockstream.info/api"


class BtcBalanceSource(BalanceSource):
    def __init__(self, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(timeout=timeout)

    @property
    def chain(self) -> str:
        return "btc"

    async def balance(self, candidate: Candidate) -> int:
        for attempt in range(3):
            try:
                r = await self._client.get(f"{BASE}/address/{candidate.address}")
                r.raise_for_status()
                data = r.json()
                chain_stats = data.get("chain_stats", {})
                funded = int(chain_stats.get("funded_txo_sum", 0))
                spent = int(chain_stats.get("spent_txo_sum", 0))
                return max(funded - spent, 0)
            except (httpx.HTTPError, KeyError, ValueError):
                if attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)
        return 0