import pytest

from paper_tunes.audio.container import pack, unpack


def test_ptm1_round_trip():
    payload = bytes(range(256)) * 100
    blob = pack(payload, shape=(4, 8, 800), bandwidth=3.0)
    header, restored = unpack(blob)
    assert restored == payload
    assert header.shape0 == 4
    assert header.shape1 == 8
    assert header.shape2 == 800
    assert header.bandwidth_tenths == 30


def test_ptm1_detects_corruption():
    blob = bytearray(pack(b"paper tunes", shape=(1, 1, 11), bandwidth=1.5))
    blob[-1] ^= 0x01
    with pytest.raises(ValueError, match="checksum"):
        unpack(bytes(blob))
