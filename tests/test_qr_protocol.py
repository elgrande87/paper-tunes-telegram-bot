import pytest

from paper_tunes.qr_protocol import assemble, decode_chunk, encode_chunk


def test_round_trip():
    value = b"hello paper tunes" * 20
    encoded = encode_chunk("abc123", 0, 1, value)
    chunk = decode_chunk(encoded)
    assert chunk.data == value
    assert assemble([chunk]) == value


def test_out_of_order_assembly():
    chunks = [
        decode_chunk(encode_chunk("s", 1, 2, b"world")),
        decode_chunk(encode_chunk("s", 0, 2, b"hello ")),
    ]
    assert assemble(chunks) == b"hello world"


def test_missing_chunk():
    chunk = decode_chunk(encode_chunk("s", 0, 2, b"hello"))
    with pytest.raises(ValueError, match="Missing chunks"):
        assemble([chunk])
