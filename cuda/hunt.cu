// cuda/hunt.cu
#include <cstdio>
#include <cstdint>
#include "pbkdf2_sha512.cuh"
#include "secp256k1.cuh"
#include "ripemd160.cuh"

// kernel receives: batch of pre-built 128-byte password blocks (mnemonics),
// shard keys, output buffer of candidates that hit.
__global__ void hunt(const uint8_t *pw, const uint64_t *keys, size_t nkeys,
                     uint32_t count, uint32_t *hits, uint8_t *hit_prefix) {
    uint32_t i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= count) return;

    uint8_t salt[64] = {0};
    const char *mp = "mnemonic";
    for (int k = 0; k < 8; k++) salt[k] = (uint8_t)mp[k];

    uint8_t seed[64];
    pbkdf2_64(pw + i * 128, salt, seed);

    uint8_t master[64];
    hmac_sha512_seed(seed, master);                    // "Bitcoin seed"
    uint8_t priv[32], chain[32];
    for (int k = 0; k < 32; k++) { priv[k] = master[k]; chain[k] = master[k + 32]; }

    // m/44'/0'/0' hardened, then /0/0 non-hardened
    ckd_hardened(priv, chain, 44); ckd_hardened(priv, chain, 0); ckd_hardened(priv, chain, 0);
    uint8_t pub[33];
    if (!ckd_normal(priv, chain, 0, pub)) return;
    if (!ckd_normal(priv, chain, 0, pub)) return;

    uint8_t h160[20];
    hash160(pub, h160);
    uint64_t key = 0;
    for (int k = 0; k < 8; k++) key = (key << 8) | h160[k];

    // binary search in shard
    long lo = 0, hi = (long)nkeys - 1;
    while (lo <= hi) {
        long mid = (lo + hi) >> 1;
        uint64_t v = keys[mid];
        if (v == key) {
            uint32_t slot = atomicAdd(hits, 1);
            for (int k = 0; k < 20; k++) hit_prefix[slot * 20 + k] = h160[k];
            return;
        }
        if (v < key) lo = mid + 1; else hi = mid - 1;
    }
}