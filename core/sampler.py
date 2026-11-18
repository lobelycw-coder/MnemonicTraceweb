"""Biased mnemonic sampler. Uniform search is hopeless; this is not uniform."""
from __future__ import annotations
import hashlib
import json
import math
import random
from pathlib import Path

from .bip39 import WORDLIST, entropy_to_mnemonic

MODELS = Path(__file__).parent / "models"


class Sampler:
    """
    wordfreq.json: {"unigram": [2048 floats], "bigram": {"<prev_idx>": [2048 floats]}}
    Build it with pipeline/build_wordfreq.py over a corpus of real mnemonics.
    Missing model -> uniform, so this still runs on day one.
    """

    def __init__(self, seed: int | None = None, temperature: float = 0.85,
                 bigram_mix: float = 0.7, top_k: int = 400):
        self.rng = random.Random(seed)
        self.temperature = temperature
        self.bigram_mix = bigram_mix
        self.top_k = top_k
        self._uni = None
        self._bi = {}
        p = MODELS / "wordfreq.json"
        if p.exists():
            d = json.loads(p.read_text())
            self._uni = d["unigram"]
            self._bi = {int(k): v for k, v in d.get("bigram", {}).items()}

    def _dist(self, prev: int | None) -> list[float]:
        if self._uni is None:
            return [1.0] * 2048
        base = self._uni
        if prev is not None and prev in self._bi:
            cond = self._bi[prev]
            base = [self.bigram_mix * c + (1 - self.bigram_mix) * u for c, u in zip(cond, base)]
        if self.temperature != 1.0:
            inv = 1.0 / self.temperature
            base = [max(w, 1e-12) ** inv for w in base]
        return base

    def _draw(self, prev: int | None) -> int:
        dist = self._dist(prev)
        if self.top_k < 2048 and self._uni is not None:
            ranked = sorted(range(2048), key=dist.__getitem__, reverse=True)[: self.top_k]
            pool = [dist[i] for i in ranked]
            idx = self.rng.choices(ranked, weights=pool, k=1)[0]
        else:
            idx = self.rng.choices(range(2048), weights=dist, k=1)[0]
        return idx

    def sample(self) -> str:
        """Return a checksum-valid 12-word mnemonic."""
        prev = None
        idxs = []
        for _ in range(11):
            prev = self._draw(prev)
            idxs.append(prev)
        packed = 0
        for i in idxs:
            packed = (packed << 11) | i          # 121 bits
        # 12th word: 7 model-chosen entropy bits + 4 checksum bits
        tail = self._draw(prev) >> 4             # top 7 bits of a plausible word
        entropy_int = (packed << 7) | tail
        entropy = entropy_int.to_bytes(16, "big")
        cs = hashlib.sha256(entropy).digest()[0] >> 4
        return entropy_to_mnemonic(entropy)[:-1] + " " + WORDLIST[(tail << 4) | cs]