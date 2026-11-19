from functools import lru_cache

from bip_utils import Bip39EntropyGenerator, Bip39MnemonicGenerator, Bip39WordsNum

ENTROPY_BITS = 128


@lru_cache(maxsize=8192)
def seed_at(index: int) -> str:
    """Deterministic BIP39 phrase for a global index (reproducible across workers)."""
    entropy = Bip39EntropyGenerator(ENTROPY_BITS).Generate()
    return Bip39MnemonicGenerator().FromEntropy(entropy)