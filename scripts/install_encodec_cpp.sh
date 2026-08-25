#!/usr/bin/env bash
set -euo pipefail

# Build PABannier/encodec.cpp outside the Python environment.
# The upstream project is a pure C/C++ implementation using ggml.
# NOTE: upstream currently lists 24 kHz model support as a roadmap item,
# so this is an experimental/native backend build, not yet the Paper Tunes
# 24 kHz production codec.

ROOT="${PT_NATIVE_DIR:-$HOME/.local/share/paper-tunes-native}"
SRC="$ROOT/encodec.cpp"
BUILD="$SRC/build"
REPO="https://github.com/PABannier/encodec.cpp.git"

if ! command -v git >/dev/null; then echo "git fehlt."; exit 1; fi
if ! command -v cmake >/dev/null; then echo "cmake fehlt. Installiere: apt install cmake build-essential"; exit 1; fi

mkdir -p "$ROOT"
if [[ ! -d "$SRC/.git" ]]; then
  git clone --recurse-submodules "$REPO" "$SRC"
else
  git -C "$SRC" pull --ff-only
  git -C "$SRC" submodule update --init --recursive
fi

cmake -S "$SRC" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
cmake --build "$BUILD" --config Release -j"${JOBS:-2}"

echo
echo "encodec.cpp gebaut:"
find "$BUILD" -maxdepth 2 -type f -perm -111 -print 2>/dev/null || true
echo
echo "Quelle: $SRC"
echo "Build:  $BUILD"
echo
echo "Wichtig: Das Upstream-Projekt führt 24-kHz-Modell-Support derzeit noch als Roadmap-Punkt."
