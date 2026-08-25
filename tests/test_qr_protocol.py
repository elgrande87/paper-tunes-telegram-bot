import base64
import hashlib

import pytest

from paper_tunes.qr_protocol import ProtocolError, assemble_chunks, parse_chunk


def encoded(file_id: str, index: int, total: int, value: bytes, checksum: bool = False) -> str:
    digest = f"|{hashlib.sha256(value).hexdigest()}" if checksum else ""
    return f"PT1|{file_id}|{index}/{total}{digest}|{base64.b64encode(value).decode()}"


def test_parse_and_assemble_out_of_order():
    chunks = [parse_chunk(encoded("song", 2, 2, b"world")), parse_chunk(encoded("song", 1, 2, b"hello "))]
    assert assemble_chunks(chunks) == ("song", b"hello world")


def test_duplicate_chunk_is_allowed():
    chunk = parse_chunk(encoded("song", 1, 1, b"audio"))
    assert assemble_chunks([chunk, chunk])[1] == b"audio"


def test_missing_chunk_is_reported():
    with pytest.raises(ProtocolError, match="Missing chunks: 2"):
        assemble_chunks([parse_chunk(encoded("song", 1, 2, b"part"))])


def test_checksum_is_validated():
    assert parse_chunk(encoded("song", 1, 1, b"audio", checksum=True)).payload == b"audio"
    bad = "PT1|song|1/1|deadbeef|" + base64.b64encode(b"audio").decode()
    with pytest.raises(ProtocolError, match="checksum"):
        parse_chunk(bad)


@pytest.mark.parametrize("value", ["", "PT1|song|0/1|YQ==", "PT1|song|2/1|YQ==", "PT1|song|1/1|***"])
def test_invalid_payloads(value):
    with pytest.raises(ProtocolError):
        parse_chunk(value)
