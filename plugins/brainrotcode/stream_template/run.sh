#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
cmake -S . -B build/Debug -DCMAKE_BUILD_TYPE=Debug
cmake --build build/Debug -j "$(nproc)"
./tools/rebuild_live.sh
exec ./build/Debug/brainrot_voxel
