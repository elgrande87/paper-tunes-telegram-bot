#!/usr/bin/env python3
"""Benchmark codec payload sizes and conservative printable QR counts."""

from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

from paper_tunes.codecs.opus import encode_wav
from paper_tunes.qr.transport import QR_CAPACITY, qr_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="runtime/test.wav")
    parser.add_argument("--bitrates", nargs="+", default=["3k", "6k", "12k"])
    parser.add_argument("--levels", nargs="+", default=["M", "Q", "H"])
    args = parser.parse_args()
    source = Path(args.input)
    if not source.exists():
        raise SystemExit(f"Fehlt: {source}")

    print(f"Input: {source} ({source.stat().st_size:,} bytes)")
    print("\nCodec      Audio bytes   PTM+QR bytes   M QR   Q QR   H QR   Encode")
    print("-------------------------------------------------------------------")
    with tempfile.TemporaryDirectory(prefix="paper-tunes-qr-bench-") as tmp:
        for bitrate in args.bitrates:
            out = Path(tmp) / f"test-{bitrate}.opus"
            t0 = time.monotonic()
            encode_wav(source, out, bitrate)
            elapsed = time.monotonic() - t0
            audio_size = out.stat().st_size
            # Add a conservative PTM/transport overhead estimate. The actual
            # PTM container is binary and the QR frame header is 18 bytes.
            ptm_size = audio_size + 64
            counts = [qr_count(ptm_size, level) for level in args.levels]
            values = dict(zip(args.levels, counts))
            print(f"Opus {bitrate:<5} {audio_size:11,}   {ptm_size:11,}   "
                  f"{values.get('M', '-'):4}   {values.get('Q', '-'):4}   {values.get('H', '-'):4}   {elapsed:6.2f}s")

    print("\nQR model: conservative binary payload budgets")
    for level in args.levels:
        print(f"  {level}: {QR_CAPACITY[level]} bytes/frame including transport header")
    print("Hinweis: Das ist noch kein gerenderter/gescannter QR-Test; echte QR-Kapazität hängt von Version, Encoding und Druckqualität ab.")


if __name__ == "__main__":
    main()
