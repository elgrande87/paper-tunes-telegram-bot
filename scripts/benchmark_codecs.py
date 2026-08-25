#!/usr/bin/env python3
"""Benchmark the Pi-friendly Opus backend and report QR-relevant sizes."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from paper_tunes.codecs.opus import encode_wav, decode_to_wav


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="runtime/test.wav")
    parser.add_argument("--bitrates", nargs="+", default=["3k", "6k", "12k"])
    args = parser.parse_args()
    source = Path(args.input)
    if not source.exists():
        raise SystemExit(f"Fehlt: {source}")
    print(f"Input: {source} ({source.stat().st_size:,} bytes)")
    print("\nCodec      Bytes       Ratio       Encode     Decode")
    print("------------------------------------------------------")
    with tempfile.TemporaryDirectory(prefix="paper-tunes-bench-") as tmp:
        for bitrate in args.bitrates:
            encoded = Path(tmp) / f"test-{bitrate}.opus"
            decoded = Path(tmp) / f"test-{bitrate}.wav"
            t0 = time.monotonic()
            encode_wav(source, encoded, bitrate)
            enc_time = time.monotonic() - t0
            t0 = time.monotonic()
            decode_to_wav(encoded, decoded)
            dec_time = time.monotonic() - t0
            size = encoded.stat().st_size
            ratio = size / source.stat().st_size
            print(f"Opus {bitrate:<5} {size:9,}   {ratio:8.3%}   {enc_time:7.2f}s   {dec_time:7.2f}s")
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found")


if __name__ == "__main__":
    main()
