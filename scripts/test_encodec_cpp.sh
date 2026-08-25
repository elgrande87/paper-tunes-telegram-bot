#!/usr/bin/env bash
set -euo pipefail

ROOT="${PT_NATIVE_DIR:-$HOME/.local/share/paper-tunes-native}"
SRC="$ROOT/encodec.cpp"
BUILD="$SRC/build"

if [[ ! -d "$SRC/.git" ]]; then
  echo "encodec.cpp ist noch nicht gebaut. Erst ausführen:"
  echo "  bash scripts/install_encodec_cpp.sh"
  exit 1
fi

if [[ ! -d "$BUILD" ]]; then
  echo "Build-Verzeichnis fehlt. Erst install_encodec_cpp.sh ausführen."
  exit 1
fi

echo "== encodec.cpp native capability test =="
git -C "$SRC" log -1 --oneline

echo
echo "Build-Artefakte:"
find "$BUILD" -maxdepth 3 -type f -perm -111 -print 2>/dev/null || true

echo
echo "Paper Tunes test.wav:"
file "${1:-runtime/test.wav}" 2>/dev/null || true

echo
echo "Hinweis: Ein echter 24-kHz-EnCodec-Roundtrip wird bewusst noch nicht behauptet."
echo "PABannier/encodec.cpp listet den 24-kHz-Modell-Support aktuell als Roadmap-Punkt."
echo "Wenn der native Build erfolgreich ist, prüfen wir als Nächstes die konkrete"
echo "Modell-/CLI-Schnittstelle und ob ein passendes Modell für unseren Pi verfügbar ist."
