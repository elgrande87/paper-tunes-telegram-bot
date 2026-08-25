"""Generate the standard Paper Tunes test WAV without external audio assets.

Output: 10 s, mono, 24 kHz, signed 16-bit PCM.
The signal combines spoken-test-style tones, silence, sweeps and a deterministic
pseudo-speech-like harmonic section so codec tests exercise more than a sine wave.
"""

from __future__ import annotations

import argparse
import math
import random
import wave
from pathlib import Path

SAMPLE_RATE = 24_000
DURATION = 10


def sample(t: float, rng: random.Random) -> float:
    # Deterministic test signal: silence -> harmonic voice-like section -> sweep
    # -> short tone sequence -> silence.
    if t < 1.0 or t >= 9.5:
        return 0.0
    if 1.0 <= t < 6.0:
        f0 = 120.0 + 18.0 * math.sin(2 * math.pi * 0.7 * t)
        value = sum((1.0 / k) * math.sin(2 * math.pi * f0 * k * t) for k in range(1, 9))
        value *= 0.55
        # Low-level deterministic noise makes the signal less artificially simple.
        value += 0.015 * rng.uniform(-1.0, 1.0)
        return value
    if 6.0 <= t < 8.5:
        x = t - 6.0
        f = 250.0 + 3000.0 * (x / 2.5)
        return 0.55 * math.sin(2 * math.pi * f * x)
    x = t - 8.5
    freqs = (261.63, 329.63, 392.00, 523.25)
    idx = min(int(x / 0.25), 3)
    return 0.55 * math.sin(2 * math.pi * freqs[idx] * (x % 0.25))


def generate(path: Path) -> None:
    rng = random.Random(20260825)
    frames = bytearray()
    for n in range(SAMPLE_RATE * DURATION):
        value = max(-1.0, min(1.0, sample(n / SAMPLE_RATE, rng)))
        frames += int(value * 32767).to_bytes(2, "little", signed=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(frames)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", default="runtime/test.wav")
    args = parser.parse_args()
    generate(Path(args.output))
    print(f"Created {args.output}: 10 s / mono / 24 kHz / 16-bit PCM")
