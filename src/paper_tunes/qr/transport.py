"""QR transport framing for Paper Tunes.

The QR payload is binary-safe and self-describing.  Each frame carries enough
metadata to reconstruct a PTM stream and reject damaged/mixed pages.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

MAGIC = b"PTQ1"
_VERSION = 1
_HEADER = struct.Struct(">4sBBHHII")

# Conservative binary payload budgets. These are deliberately below the
# theoretical QR maximum so printed/photographed codes have useful margin.
QR_CAPACITY = {
    "M": 140,
    "Q": 110,
    "H": 80,
}


@dataclass(frozen=True)
class FrameInfo:
    index: int
    total: int
    payload_size: int
    crc32: int


def split(payload: bytes, *, chunk_size: int = QR_CAPACITY["Q"]) -> list[bytes]:
    if chunk_size < _HEADER.size + 1:
        raise ValueError("chunk_size is too small")
    if not payload:
        return [_HEADER.pack(MAGIC, _VERSION, 0, 1, 0, 0, 0)]
    total = (len(payload) + (chunk_size - _HEADER.size) - 1) // (chunk_size - _HEADER.size)
    frames: list[bytes] = []
    for index in range(total):
        part = payload[index * (chunk_size - _HEADER.size):(index + 1) * (chunk_size - _HEADER.size)]
        crc = zlib.crc32(part) & 0xFFFFFFFF
        frames.append(_HEADER.pack(MAGIC, _VERSION, 0, index, total, len(part), crc) + part)
    return frames


def inspect(frame: bytes) -> FrameInfo:
    if len(frame) < _HEADER.size:
        raise ValueError("QR frame is too short")
    magic, version, flags, index, total, size, crc = _HEADER.unpack(frame[:_HEADER.size])
    if magic != MAGIC or version != _VERSION or flags != 0:
        raise ValueError("Unsupported Paper Tunes QR frame")
    payload = frame[_HEADER.size:]
    if size != len(payload):
        raise ValueError("QR frame payload size mismatch")
    if zlib.crc32(payload) & 0xFFFFFFFF != crc:
        raise ValueError("QR frame checksum mismatch")
    if total == 0 or index >= total:
        raise ValueError("Invalid QR frame sequence")
    return FrameInfo(index=index, total=total, payload_size=size, crc32=crc)


def qr_count(payload_size: int, level: str = "Q") -> int:
    if level not in QR_CAPACITY:
        raise ValueError(f"unknown QR error correction level: {level}")
    capacity = QR_CAPACITY[level] - _HEADER.size
    if payload_size <= 0:
        return 1
    return (payload_size + capacity - 1) // capacity
