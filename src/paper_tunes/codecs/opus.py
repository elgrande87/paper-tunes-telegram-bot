"""Small local Opus backend using the system FFmpeg binary.

Using FFmpeg keeps the Python side lightweight on Raspberry Pi/DietPi while
still giving us a deterministic, widely available Opus implementation.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _ffmpeg() -> str:
    binary = shutil.which("ffmpeg")
    if not binary:
        raise RuntimeError("ffmpeg is required for the Opus backend")
    return binary


def encode_wav(input_path: str | Path, output_path: str | Path, bitrate: str = "6k") -> None:
    subprocess.run([
        _ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(input_path), "-map_metadata", "-1",
        "-c:a", "libopus", "-b:a", bitrate, "-vbr", "off",
        "-application", "audio", str(output_path),
    ], check=True)


def decode_to_wav(input_path: str | Path, output_path: str | Path) -> None:
    subprocess.run([
        _ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(input_path), "-ar", "24000", "-ac", "1",
        "-c:a", "pcm_s16le", str(output_path),
    ], check=True)
