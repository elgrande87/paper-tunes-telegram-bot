from __future__ import annotations

import base64
import binascii
import hashlib
import re
from dataclasses import dataclass


class ProtocolError(ValueError):
    """Raised when a Paper Tunes QR payload is malformed or incomplete."""


@dataclass(frozen=True)
class Chunk:
    file_id: str
    index: int
    total: int
    payload: bytes
    checksum: str | None = None


_HEADER = re.compile(
    r"^PT1\|(?P<file_id>[A-Za-z0-9_-]{1,64})\|(?P<index>\d+)/(?P<total>\d+)"
    r"(?:\|(?P<checksum>[0-9a-fA-F]{8,64}))?\|(?P<data>.+)$",
    re.DOTALL,
)


def parse_chunk(value: str | bytes) -> Chunk:
    """Parse ``PT1|file-id|index/total|[sha256|]base64`` QR data."""
    if isinstance(value, bytes):
        try:
            value = value.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ProtocolError("QR data is not ASCII") from exc

    match = _HEADER.fullmatch(value.strip())
    if not match:
        raise ProtocolError("Unsupported QR payload")

    index = int(match["index"])
    total = int(match["total"])
    if total < 1 or index < 1 or index > total:
        raise ProtocolError("Invalid chunk index")

    try:
        payload = base64.b64decode(match["data"], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ProtocolError("Invalid base64 payload") from exc

    checksum = match["checksum"]
    if checksum and not hashlib.sha256(payload).hexdigest().startswith(checksum.lower()):
        raise ProtocolError("Chunk checksum mismatch")

    return Chunk(match["file_id"], index, total, payload, checksum)


def assemble_chunks(chunks: list[Chunk]) -> tuple[str, bytes]:
    """Validate and assemble one complete Paper Tunes file."""
    if not chunks:
        raise ProtocolError("No chunks found")

    file_id = chunks[0].file_id
    total = chunks[0].total
    by_index: dict[int, bytes] = {}
    for chunk in chunks:
        if chunk.file_id != file_id or chunk.total != total:
            raise ProtocolError("QR codes belong to different files")
        old = by_index.get(chunk.index)
        if old is not None and old != chunk.payload:
            raise ProtocolError(f"Conflicting chunk {chunk.index}")
        by_index[chunk.index] = chunk.payload

    missing = [str(index) for index in range(1, total + 1) if index not in by_index]
    if missing:
        raise ProtocolError("Missing chunks: " + ", ".join(missing))

    return file_id, b"".join(by_index[index] for index in range(1, total + 1))
