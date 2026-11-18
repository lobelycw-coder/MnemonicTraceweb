import asyncio

import httpx

from domain.models import Candidate
from ports.balance_source import BalanceSource

LAMPORTS = 10**9


class SolanaBalanceSource(BalanceSource):
    def __init__(self, rpc_url: str, timeout: float = 10.0) -> None:
        self._url = rpc_url
        self._client = httpx.AsyncClient(timeout=timeout)

    @property
    def chain(self) -> str:
        return "sol"

    async def balance(self, candidate: Candidate) -> int:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [candidate.address]}
        for attempt in range(3):
            try:
                r = await self._client.post(self._url, json=payload)
                r.raise_for_status()
                return int(r.json()["result"]["value"])
            except (httpx.HTTPError, KeyError, ValueError):
                if attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)
        return 0