shard-<idx>.bin   sorted uint64 BE, 8 bytes each
manifest.json     {"count": N, "shards": M, "built": ISO8601, "chains": [...]}
Probe: mmap -> binary search 8-byte prefix -> on hit, expand full tree + live-verify
FP rate at 1e9 keys in 64-bit space: negligible; hits are re-verified against live nodes.