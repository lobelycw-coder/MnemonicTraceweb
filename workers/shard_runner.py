from adapters.balance.btc_blockstream import BtcBalanceSource
from domain.seeds import seed_at
import asyncio
import logging
import os
from uuid import uuid4

from adapters.accel.cpu_backend import CpuBackend
from adapters.balance.evm_etherscan import EvmBalanceSource
from adapters.balance.solana_rpc import SolanaBalanceSource
from adapters.db.models import HitRow
from adapters.db.session import session_factory
from adapters.store.pg_shard_store import PgShardStore
from domain.derivation import derive_addresses
from domain.models import Candidate

log = logging.getLogger("runner")
CHAINS = ("eth", "sol", "btc")


def build_balance_sources() -> dict[str, object]:
    return {
        ""btc": BtcBalanceSource(),
        "eth": EvmBalanceSource(os.environ["ETHERSCAN_KEY"]),
        "sol": SolanaBalanceSource(os.environ["SOLANA_RPC"]),
    }


class ShardRunner:
    def __init__(self) -> None:
        self._store = PgShardStore(session_factory)
        self._accel = CpuBackend(concurrency=int(os.environ.get("DERIVE_CONCURRENCY", "2")))
        self._balances = build_balance_sources()
        self._worker_id = f"w-{uuid4().hex[:8]}"

    async def run(self) -> None:
        while True:
            shard = await self._store.claim(self._worker_id)
            if shard is None:
                log.info("no pending shards, idling")
                await asyncio.sleep(15)
                continue
            try:
                await self._process(shard.id, shard.start_index, shard.end_index)
                await self._store.complete(shard.id)
            except Exception as exc:  # noqa: BLE001
                log.exception("shard %s failed", shard.id)
                await self._store.fail(shard.id, str(exc)[:250])

    async def _process(self, shard_id: int, start: int, end: int) -> None:
        seeds = [seed_at(i) for i in range(start, end)]
        candidates = await self._accel.derive_batch(seeds, CHAINS)
        for cand in candidates:
            source = self._balances.get(cand.chain)
            if source is None:
                continue
            try:
                bal = await source.balance(cand)
            except Exception:  # noqa: BLE001
                continue
            if bal > 0:
                await self._record_hit(shard_id, cand, bal)

    async def _record_hit(self, shard_id: int, cand: Candidate, balance: int) -> None:
        async with session_factory() as session:
            async with session.begin():
                session.add(
                    HitRow(
                        shard_id=shard_id,
                        chain=cand.chain,
                        address=cand.address,
                        seed=cand.seed,
                        balance=balance,
                    )
                )
                
                async def close(self) -> None:
        for source in self._balances.values():
            await source.close()