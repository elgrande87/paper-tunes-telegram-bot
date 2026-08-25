"""QR generation and decoding primitives."""

from __future__ import annotations

import cv2
import qrcode
from PIL import Image

from .qr_protocol import Chunk, decode_chunk, encode_chunk


def split_bytes(data: bytes, chunk_size: int) -> list[bytes]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)] or [b""]


def make_qr_images(data: bytes, session: str, chunk_size: int = 700) -> list[Image.Image]:
    chunks = split_bytes(data, chunk_size)
    total = len(chunks)
    images: list[Image.Image] = []
    for index, chunk in enumerate(chunks):
        text = encode_chunk(session, index, total, chunk)
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        images.append(qr.make_image())
    return images


def decode_qr_image(image: Image.Image) -> list[Chunk]:
    detector = cv2.QRCodeDetector()
    frame = cv2.cvtColor(__import__("numpy").array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    values, _, _ = detector.detectAndDecodeMulti(frame)
    if values is None:
        value, _, _ = detector.detectAndDecode(frame)
        values = [value] if value else []
    result = []
    for value in values:
        if value:
            result.append(decode_chunk(value))
    return result
