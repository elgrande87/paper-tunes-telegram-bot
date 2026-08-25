#!/usr/bin/env python3
"""Run the deterministic WAV through EnCodec/PTM1 and report sizes.

This intentionally does not require Telegram or QR codes yet. It validates the
core audio representation before we add the printable-paper layer.
"""

from __future__ import annotations

import argparse
import hashlib
import time
from pathlib import Path

from paper_tunes.audio.encodec_codec import EnCodecAudio


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="runtime/test.wav")
    parser.add_argument("output", nargs="?", default="runtime/test-restored.wav")
    parser.add_argument("--bandwidth", type=float, default=3.0)
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.output)
    if not source.exists():
        raise SystemExit(f"Testdatei fehlt: {source}. Zuerst scripts/generate_test_wav.py ausführen.")

    codec = EnCodecAudio(bandwidth=args.bandwidth)
    start = time.monotonic()
    ptm = codec.encode_file(str(source))
    encode_seconds = time.monotonic() - start
    output.parent.mkdir(parents=True, exist_ok=True)
    ptm_path = output.with_suffix(".ptm")
    ptm_path.write_bytes(ptm)

    start = time.monotonic()
    codec.decode_to_wav(ptm, str(output))
    decode_seconds = time.monotonic() - start

    original = source.read_bytes()
    restored = output.read_bytes()
    print(f"Original:       {source} ({len(original):,} bytes)")
    print(f"PTM1:           {ptm_path} ({len(ptm):,} bytes)")
    print(f"Restored WAV:   {output} ({len(restored):,} bytes)")
    print(f"PTM/original:   {len(ptm) / len(original):.4%}")
    print(f"Encode time:    {encode_seconds:.2f} s")
    print(f"Decode time:    {decode_seconds:.2f} s")
    print(f"Original SHA256: {hashlib.sha256(original).hexdigest()}")
    print(f"Restored SHA256: {hashlib.sha256(restored).hexdigest()}")
    print("Hinweis: Bei verlustbehaftetem EnCodec müssen die WAV-Dateien nicht byte-identisch sein.")


if __name__ == "__main__":
    main()
