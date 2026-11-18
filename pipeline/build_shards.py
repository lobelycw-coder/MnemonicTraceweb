"""pipeline/build_shards.py — address list -> sorted truncated-hash shards."""
import hashlib, json, sys, time
from pathlib import Path

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PREFIX = 8

def b58decode(s: str) -> bytes:
    n = 0
    for c in s:
        n = n * 58 + B58.index(c)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return b"\x00" * (len(s) - len(s.lstrip("1"))) + raw

def addr_to_hash160(addr: str) -> bytes | None:
    try:
        if addr.startswith("0x"):
            return bytes.fromhex(addr[2:].rjust(40, "0")[-40:])
        payload = b58decode(addr)[:-4]
        return payload[-20:]
    except Exception:
        return None

def main(src: str, outdir: str, shard_mb: int = 512):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    keys = set()
    with open(src) as f:
        for line in f:
            h = addr_to_hash160(line.strip())
            if h: keys.add(h[:PREFIX])
    ordered = sorted(keys)
    per = shard_mb * 1024 * 1024 // PREFIX
    shards = 0
    for i in range(0, len(ordered), per):
        chunk = ordered[i:i + per]
        (out / f"shard-{shards:05d}.bin").write_bytes(b"".join(chunk))
        shards += 1
    (out / "manifest.json").write_text(json.dumps(
        {"count": len(ordered), "shards": shards, "prefix": PREFIX, "built": time.strftime("%Y-%m-%dT%H:%M:%SZ")}))
    print(f"{len(ordered)} keys -> {shards} shards")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])