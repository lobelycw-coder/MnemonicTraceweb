"""core/probe.py"""
import json, mmap, os
from pathlib import Path

class Shard:
    def __init__(self, path: Path):
        self.f = open(path, "rb")
        self.mm = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        self.n = len(self.mm) // 8

    def contains(self, prefix: bytes) -> bool:
        key = prefix[:8]
        lo, hi = 0, self.n - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            v = self.mm[mid * 8: mid * 8 + 8]
            if v == key: return True
            if v < key: lo = mid + 1
            else: hi = mid - 1
        return False

def load_shards(dirpath: str) -> list[Shard]:
    return [Shard(p) for p in sorted(Path(dirpath).glob("shard-*.bin"))]