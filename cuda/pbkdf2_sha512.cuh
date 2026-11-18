// cuda/pbkdf2_sha512.cuh
#pragma once
#include "sha512.cuh"

// HMAC-SHA512 over a 128-byte password block, pad precomputed once per candidate.
struct HMACPads { SHA512State inner; SHA512State outer; };

__device__ __forceinline__ void hmac_pads(const uint8_t pw[128], HMACPads &p) {
    uint8_t blk[128];
    sha512_init(p.inner); sha512_init(p.outer);
    #pragma unroll
    for (int i = 0; i < 128; i++) blk[i] = pw[i] ^ 0x36;
    sha512_block(p.inner, blk);
    #pragma unroll
    for (int i = 0; i < 128; i++) blk[i] = pw[i] ^ 0x5c;
    sha512_block(p.outer, blk);
}

// U = HMAC(pw, msg64) using precomputed pads. msg64 padded to one 128-byte block.
__device__ __forceinline__ void hmac64(const HMACPads &p, const uint8_t msg[64], uint8_t out[64]) {
    uint8_t blk[128];
    SHA512State s = p.inner;
    #pragma unroll
    for (int i = 0; i < 64; i++) blk[i] = msg[i];
    blk[64] = 0x80;
    #pragma unroll
    for (int i = 65; i < 126; i++) blk[i] = 0;
    blk[126] = 0x02; blk[127] = 0x80;          // 1024-bit length
    sha512_block(s, blk);
    uint8_t inner_digest[64];
    #pragma unroll
    for (int i = 0; i < 8; i++) {
        uint64_t v = s.h[i];
        inner_digest[i*8]  = v>>56; inner_digest[i*8+1] = v>>48; inner_digest[i*8+2] = v>>40; inner_digest[i*8+3] = v>>32;
        inner_digest[i*8+4]= v>>24; inner_digest[i*8+5] = v>>16; inner_digest[i*8+6] = v>>8;  inner_digest[i*8+7] = v;
    }
    SHA512State o = p.outer;
    #pragma unroll
    for (int i = 0; i < 64; i++) blk[i] = inner_digest[i];
    blk[64] = 0x80;
    #pragma unroll
    for (int i = 65; i < 126; i++) blk[i] = 0;
    blk[126] = 0x02; blk[127] = 0x80;
    sha512_block(o, blk);
    #pragma unroll
    for (int i = 0; i < 8; i++) {
        uint64_t v = o.h[i];
        out[i*8]  = v>>56; out[i*8+1] = v>>48; out[i*8+2] = v>>40; out[i*8+3] = v>>32;
        out[i*8+4]= v>>24; out[i*8+5] = v>>16; out[i*8+6] = v>>8;  out[i*8+7] = v;
    }
}

// Full PBKDF2-HMAC-SHA512, dkLen = 64 (one block), 2048 rounds.
__device__ __forceinline__ void pbkdf2_64(const uint8_t pw[128], const uint8_t salt[64], uint8_t dk[64]) {
    HMACPads p; hmac_pads(pw, p);
    uint8_t msg[64];
    #pragma unroll
    for (int i = 0; i < 64; i++) msg[i] = salt[i];
    msg[60] = 0; msg[61] = 0; msg[62] = 0; msg[63] = 1;   // INT32BE block index
    hmac64(p, msg, dk);
    uint8_t u[64];
    #pragma unroll
    for (int i = 0; i < 64; i++) u[i] = dk[i];
    for (int r = 1; r < 2048; r++) {
        hmac64(p, u, u);
        #pragma unroll
        for (int i = 0; i < 64; i++) dk[i] ^= u[i];
    }
}