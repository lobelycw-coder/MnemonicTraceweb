"""Reference derivation. Slow, correct, used to validate the GPU kernel."""
from __future__ import annotations
import hashlib
import hmac
import unicodedata

P = 2**256 - 2**32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)

def _add(a, b):
    if a is None: return b
    if b is None: return a
    if a[0] == b[0] and (a[1] + b[1]) % P == 0: return None
    if a == b:
        l = 3 * a[0] * a[0] * pow(2 * a[1], -1, P) % P
    else:
        l = (b[1] - a[1]) * pow(b[0] - a[0], -1, P) % P
    x = (l * l - a[0] - b[0]) % P
    return (x, (l * (a[0] - x) - a[1]) % P)

def _mul(k, pt):
    r = None
    while k:
        if k & 1: r = _add(r, pt)
        pt = _add(pt, pt); k >>= 1
    return r

def pubkey_compressed(priv: int) -> bytes:
    x, y = _mul(priv, G)
    return bytes([2 + (y & 1)]) + x.to_bytes(32, "big")

def hash160(b: bytes) -> bytes:
    return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()

def master_from_mnemonic(mnemonic: str, passphrase: str = "") -> tuple[int, bytes]:
    m = unicodedata.normalize("NFKD", mnemonic).encode()
    s = b"mnemonic" + unicodedata.normalize("NFKD", passphrase).encode()
    seed = hashlib.pbkdf2_hmac("sha512", m, s, 2048, 64)
    I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    return int.from_bytes(I[:32], "big"), I[32:]

def _ckd_priv(priv: int, chain: bytes, index: int, hardened: bool) -> tuple[int, bytes]:
    data = b"\x00" + priv.to_bytes(32, "big") if hardened else pubkey_compressed(priv)
    I = hmac.new(chain, data + index.to_bytes(4, "big"), hashlib.sha512).digest()
    return (int.from_bytes(I[:32], "big") + priv) % N, I[32:]

def first_p2pkh(mnemonic: str, path=(44, 0, 0, 0, 0), passphrase: str = "") -> bytes:
    """Returns hash160 of m/44'/0'/0'/0/0 by default."""
    priv, chain = master_from_mnemonic(mnemonic, passphrase)
    for depth, idx in enumerate(path):
        priv, chain = _ckd_priv(priv, chain, idx, hardened=depth < 4)
    return hash160(pubkey_compressed(priv))