import asyncio

import httpx

from domain.models import Candidate
from ports.balance_source import BalanceSource

BASE = "https://api.etherscan.io/api"
WEI = 10**18


class EvmBalanceSource(BalanceSource):
    def __init__(self, api_key: str, timeout: float = 10.0) -> None:
        self._key = api_key
        self._client = httpx.AsyncClient(timeout=timeout)

    @property
    def chain(self) -> str:
        return "eth"

    async def balance(self, candidate: Candidate) -> int:
        params = {
            "module": "account",
            "action": "balance",
            "address": candidate.address,
            "tag": "latest",
            "apikey": self._key,
        }
        for attempt in range(3):
            try:
                r = await self._client.get(BASE, params=params)
                r.raise_for_status()
                return int(r.json().get("result", 0))
            except (httpx.HTTPError, ValueError):
                if attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)
        return 0