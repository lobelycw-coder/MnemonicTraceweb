from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Candidate:
    chain: str
    address: str
    seed: str
    index: int


@dataclass(frozen=True, slots=True)
class Shard:
    id: int
    start_index: int
    end_index: int