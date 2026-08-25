"""PTM1 container for self-describing Paper Tunes codec payloads."""

from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass

MAGIC = b"PTM1"
VERSION = 1
_CODEC_ENCODEC_24KHZ = 1

# magic, version, codec, bandwidth/10, channels, sample_rate,
# shape[0], shape[1], shape[2], sha256(compressed payload)
_HEADER = struct.Struct(">4sBBBBIQQQ32s")


@dataclass(frozen=True)
class PTMHeader:
    codec: int
    bandwidth_tenths: int
    channels: int
    sample_rate: int
    shape0: int
    shape1: int
    shape2: int
    payload_size: int
    digest: bytes


def pack(
    codes: bytes,
    *,
    shape: tuple[int, int, int],
    bandwidth: float,
    channels: int = 1,
    sample_rate: int = 24_000,
) -> bytes:
    if len(shape) != 3 or any(x < 0 for x in shape):
        raise ValueError("shape must contain three non-negative integers")
    if bandwidth <= 0 or bandwidth > 25.5:
        raise ValueError("bandwidth must be between 0 and 25.5 kbit/s")
    if channels < 1 or channels > 255:
        raise ValueError("unsupported channel count")
    if sample_rate < 1:
        raise ValueError("unsupported sample rate")

    compressed = zlib.compress(codes, level=9)
    digest = hashlib.sha256(compressed).digest()
    header = _HEADER.pack(
        MAGIC,
        VERSION,
        _CODEC_ENCODEC_24KHZ,
        round(bandwidth * 10),
        channels,
        sample_rate,
        shape[0],
        shape[1],
        shape[2],
        digest,
    )
    return header + compressed


def unpack(blob: bytes) -> tuple[PTMHeader, bytes]:
    if len(blob) < _HEADER.size:
        raise ValueError("PTM payload is too short")

    raw = _HEADER.unpack(blob[:_HEADER.size])
    magic, version, codec, bw, channels, sample_rate, s0, s1, s2, digest = raw
    if magic != MAGIC or version != VERSION:
        raise ValueError("Unsupported PTM container")
    if codec != _CODEC_ENCODEC_24KHZ:
        raise ValueError("Unsupported PTM codec")

    compressed = blob[_HEADER.size:]
    if hashlib.sha256(compressed).digest() != digest:
        raise ValueError("PTM payload checksum mismatch")
    try:
        codes = zlib.decompress(compressed)
    except zlib.error as exc:
        raise ValueError("Invalid compressed PTM payload") from exc

    header = PTMHeader(
        codec, bw, channels, sample_rate, s0, s1, s2, len(compressed), digest
    )
    return header, codes
