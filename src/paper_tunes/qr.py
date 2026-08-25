from __future__ import annotations

import cv2
import numpy as np


class QRDecodeError(ValueError):
    pass


def _variants(image: np.ndarray):
    yield image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    yield gray
    yield cv2.equalizeHist(gray)
    yield cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    for scale in (1.5, 2.0):
        yield cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)


def decode_qr_codes(image_bytes: bytes) -> list[str]:
    """Return all unique QR payloads found in an uploaded image."""
    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise QRDecodeError("The upload is not a supported image")

    detector = cv2.QRCodeDetector()
    results: list[str] = []
    for variant in _variants(image):
        try:
            found, decoded, _points, _straight = detector.detectAndDecodeMulti(variant)
        except cv2.error:
            found, decoded = False, ()
        if found:
            results.extend(value for value in decoded if value)

        value, _points, _straight = detector.detectAndDecode(variant)
        if value:
            results.append(value)

    unique = list(dict.fromkeys(results))
    if not unique:
        raise QRDecodeError("No readable QR code found")
    return unique
