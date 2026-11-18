from functools import lru_cache
from bip_utils import (
    Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip49, Bip84,
)
from domain.models import Candidate

CHAIN_REGISTRY: dict[str, object] = {
    "eth": Bip44Coins.ETHEREUM,
    "btc": Bip44Coins.BITCOIN,
    "sol": Bip44Coins.SOLANA,
}

@lru_cache(maxsize=4096)
def derive_addresses(seed_phrase: str, chains: tuple[str, ...]) -> tuple[Candidate, ...]:
    seed_bytes = Bip39SeedGenerator(seed_phrase).Generate()
    out = []
    for chain in chains:
        coin = CHAIN_REGISTRY[chain]
        acct = Bip44.FromSeed(seed_bytes, coin).Purpose().Coin().Account(0)
        for idx in range(20):
            addr = acct.Change(Bip44Changes.CHAIN_EXT).AddressIndex(idx).PublicKey().ToAddress()
            out.append(Candidate(chain=chain, address=addr, seed=seed_phrase, index=idx))
    return tuple(out)