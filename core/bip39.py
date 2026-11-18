"""BIP39 encode/decode. The checksum filter lives here."""
from __future__ import annotations
import hashlib
import unicodedata
from pathlib import Path

_WL_PATH = Path(__file__).parent / "models" / "english.txt"
WORDLIST = [w.strip() for w in _WL_PATH.read_text(encoding="utf-8").splitlines() if w.strip()]
if len(WORDLIST) != 2048:
    raise RuntimeError(f"wordlist must have 2048 entries, got {len(WORDLIST)}")
INDEX = {w: i for i, w in enumerate(WORDLIST)}


def entropy_to_mnemonic(entropy: bytes) -> str:
    ent_bits = len(entropy) * 8
    if ent_bits not in (128, 160, 192, 224, 256):
        raise ValueError("entropy must be 16/20/24/28/32 bytes")
    cs_bits = ent_bits // 32
    checksum = hashlib.sha256(entropy).digest()
    packed = (int.from_bytes(entropy, "big") << cs_bits) | (int.from_bytes(checksum, "big") >> (256 - cs_bits))
    n_words = (ent_bits + cs_bits) // 11
    out = []
    for i in range(n_words):
        out.append(WORDLIST[(packed >> (11 * (n_words - 1 - i))) & 0x7FF])
    return " ".join(out)


def mnemonic_to_entropy(mnemonic: str) -> bytes:
    words = unicodedata.normalize("NFKD", mnemonic).split()
    if len(words) not in (12, 15, 18, 21, 24):
        raise ValueError("bad word count")
    packed = 0
    for w in words:
        try:
            packed = (packed << 11) | INDEX[w]
        except KeyError:
            raise ValueError(f"not in wordlist: {w}")
    total_bits = len(words) * 11
    cs_bits = total_bits // 33
    ent_bits = total_bits - cs_bits
    entropy = (packed >> cs_bits).to_bytes(ent_bits // 8, "big")
    expected = hashlib.sha256(entropy).digest()
    expected_int = int.from_bytes(expected, "big") >> (256 - cs_bits)
    if (packed & ((1 << cs_bits) - 1)) != expected_int:
        raise ValueError("checksum mismatch")
    return entropy


def is_valid(mnemonic: str) -> bool:
    """Fast filter. Never raises."""
    try:
        mnemonic_to_entropy(mnemonic)
        return True
    except (ValueError, KeyError):
        return False


def repair_last_word(mnemonic: str) -> str:
    """Fix a single wrong/absent final word."""
    words = mnemonic.split()
    if len(words) not in (12, 15, 18, 21, 24):
        raise ValueError("bad word count")
    head = words[:-1]
    total_bits = len(words) * 11
    cs_bits = total_bits // 33
    ent_bits = total_bits - cs_bits
    packed = 0
    for w in head:
        packed = (packed << 11) | INDEX[w]
    tail_entropy_bits = ent_bits - len(head) * 11
    entropy = ((packed << tail_entropy_bits) | 0).to_bytes(ent_bits // 8, "big")
    # brute the missing entropy bits, keep whichever yields a valid checksum
    for guess in range(1 << tail_entropy_bits):
        cand_ent = ((packed << tail_entropy_bits) | guess).to_bytes(ent_bits // 8, "big")
        full = entropy_to_mnemonic(cand_ent).split()
        if full[:-1] == head:
            return " ".join(full)
    raise ValueError("unrepairable")