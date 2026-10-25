#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$here/live"
tmp="$here/live/live_rules.so.build.$$"
trap 'rm -f "$tmp"' EXIT
c++ -std=c++17 -O2 -fPIC -shared -I"$here/include" "$here/src/live_rules.cpp" -o "$tmp"
mv -f "$tmp" "$here/live/live_rules.so"
echo "Live module updated; the running game will reload it."
