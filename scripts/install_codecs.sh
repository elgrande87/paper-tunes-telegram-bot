#!/usr/bin/env bash
set -euo pipefail

# Install the Pi-friendly codec toolchain. Opus is used immediately by Paper Tunes.
# encodec.cpp is built as an experimental native backend, but its upstream
# project currently lists 24 kHz model support as a roadmap item, so it is not
# selected automatically for our 24 kHz Paper Tunes format.

if [[ "$(id -u)" -eq 0 ]]; then SUDO=""; else SUDO="sudo"; fi

$SUDO apt-get update
$SUDO apt-get install -y ffmpeg opus-tools cmake build-essential git

PREFIX="${PT_NATIVE_DIR:-$HOME/.local/src}"
mkdir -p "$PREFIX"
if [[ ! -d "$PREFIX/encodec.cpp/.git" ]]; then
  git clone --recurse-submodules https://github.com/PABannier/encodec.cpp.git "$PREFIX/encodec.cpp"
else
  git -C "$PREFIX/encodec.cpp" pull --ff-only
  git -C "$PREFIX/encodec.cpp" submodule update --init --recursive
fi

cmake -S "$PREFIX/encodec.cpp" -B "$PREFIX/encodec.cpp/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$PREFIX/encodec.cpp/build" --config Release -j"$(nproc)"

echo
echo "Opus: einsatzbereit über ffmpeg/libopus."
echo "EnCodec.cpp: gebaut unter $PREFIX/encodec.cpp/build"
echo "Hinweis: EnCodec.cpp unterstützt laut Upstream-Roadmap derzeit noch nicht das 24-kHz-Modell; Paper Tunes verwendet deshalb vorerst Opus als nativen Pi-Benchmark."
