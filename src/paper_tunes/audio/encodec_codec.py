"""EnCodec 24 kHz codec adapter for the PTM1 container."""

from __future__ import annotations

import os

import numpy as np
import torch
import torchaudio
from encodec import EncodecModel
from encodec.utils import convert_audio

from .container import pack, unpack


class EnCodecAudio:
    """Encode and decode audio using Meta EnCodec 24 kHz."""

    def __init__(self, bandwidth: float = 3.0, device: str | None = None):
        if bandwidth not in (1.5, 3.0, 6.0, 12.0, 24.0):
            raise ValueError("Unsupported EnCodec bandwidth")
        self.bandwidth = bandwidth
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = EncodecModel.encodec_model_24khz()
        self.model.set_target_bandwidth(bandwidth)
        self.model.eval().to(self.device)

    def encode_file(self, audio_path: str) -> bytes:
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(audio_path)
        wav, sr = torchaudio.load(audio_path)
        wav = convert_audio(wav, sr, self.model.sample_rate, self.model.channels)
        wav = wav.unsqueeze(0).to(self.device)
        with torch.inference_mode():
            frames = self.model.encode(wav)
        # EnCodec returns a list of (codes, scale) frames. Keep frame boundaries;
        # this first implementation targets single-frame files and rejects others.
        if len(frames) != 1:
            raise ValueError("Audio is split into multiple EnCodec frames; streaming container support is not implemented yet")
        codes = frames[0][0].detach().cpu().numpy().astype(np.int16)
        return pack(
            codes.tobytes(),
            shape=tuple(int(x) for x in codes.shape),
            bandwidth=self.bandwidth,
            channels=self.model.channels,
            sample_rate=self.model.sample_rate,
        )

    def decode_to_wav(self, ptm: bytes, output_path: str) -> None:
        header, payload = unpack(ptm)
        shape = (header.shape0, header.shape1, header.shape2)
        codes = np.frombuffer(payload, dtype=np.int16).reshape(shape)
        tensor = torch.from_numpy(codes.copy()).to(self.device).long()
        with torch.inference_mode():
            wav = self.model.decode([(tensor, None)])
        wav = wav.squeeze(0).detach().cpu()
        torchaudio.save(output_path, wav, self.model.sample_rate)
