"""QR payload protocol used by Paper Tunes.

The QR code contains a compact text envelope. The envelope is deliberately
independent from the audio codec so the codec can be replaced later.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

MAGIC = "PT1"


@dataclass(frozen=True)
class Chunk:
    session: str
    index: int
    total: int
    data: bytes
    digest: str

    @property
    def valid(self) -> bool:
        return hashlib.sha256(self.data).hexdigest()[:12] == self.digest


def encode_chunk(session: str, index: int, total: int, data: bytes) -> str:
    if not session or ":" in session:
        raise ValueError("Invalid session id")
    if total < 1 or not 0 <= index < total:
        raise ValueError("Invalid chunk index/total")
    digest = hashlib.sha256(data).hexdigest()[:12]
    payload = base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")
    return f"{MAGIC}:{session}:{index}:{total}:{digest}:{payload}"


def decode_chunk(value: str) -> Chunk:
    parts = value.split(":", 5)
    if len(parts) != 6 or parts[0] != MAGIC:
        raise ValueError("Not a Paper Tunes QR payload")
    _, session, index_s, total_s, digest, payload = parts
    try:
        index = int(index_s)
        total = int(total_s)
        data = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("Malformed Paper Tunes QR payload") from exc
    chunk = Chunk(session, index, total, data, digest)
    if not chunk.valid:
        raise ValueError("Chunk checksum mismatch")
    return chunk


def assemble(chunks: list[Chunk]) -> bytes:
    if not chunks:
        raise ValueError("No chunks supplied")
    session = chunks[0].session
    total = chunks[0].total
    if any(c.session != session or c.total != total for c in chunks):
        raise ValueError("Chunks belong to different sessions")
    unique = {c.index: c for c in chunks}
    missing = [i for i in range(total) if i not in unique]
    if missing:
        raise ValueError(f"Missing chunks: {', '.join(map(str, missing))}")
    return b"".join(unique[i].data for i in range(total))
