#!/usr/bin/env bash
set -euo pipefail
nvcc -O3 -arch=sm_86 --use_fast_math -lineinfo -o hunt hunt.cu
# sm_86 = RTX 30-series, sm_89 = 40-series. Match your rented card.
