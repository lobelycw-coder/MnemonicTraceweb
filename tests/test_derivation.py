from domain.derivation import derive_addresses
from domain.seeds import seed_at

KNOWN = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"


def test_deterministic_seeds():
    assert seed_at(42) == seed_at(42)
    assert seed_at(42) != seed_at(43)


def test_known_seed_eth_address():
    addrs = derive_addresses(KNOWN, ("eth",))
    assert addrs[0].address.lower() == "0x9858effd232b4033e47d90003d41ec34ecaeda94"


def test_all_chains_derive():
    addrs = derive_addresses(KNOWN, ("eth", "sol", "btc"))
    assert {c.chain for c in addrs} == {"eth", "sol", "btc"}
    assert len(addrs) == 60  # 20 per chain 