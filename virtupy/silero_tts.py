import io
import torch
from scipy.io import wavfile
import numpy as np


class SileroTTS:
    def __init__(self, language: str = "ru", speaker: str = "xenia", sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.speaker = speaker
        self.model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language=language,
            speaker=f"v3_1_{language}"
        )

    def __call__(self, text: str) -> bytes:
        audio = self.model.apply_tts(text=text, speaker=self.speaker, sample_rate=self.sample_rate)
        audio_np = (audio.numpy() * 32767).astype(np.int16)
        buffer = io.BytesIO()
        wavfile.write(buffer, self.sample_rate, audio_np)
        buffer.seek(0)
        return buffer.read()
