import io

import wave
from vosk_tts import Synth, Model


def to_wav(audio, channels=1, sampwidth=2, framerate=22050):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels) 
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.getvalue()


class TTS:
    def __init__(self, model_name: str = "vosk-model-tts-ru-0.6-multi"):
        self.model = Synth(Model(model_name=model_name))

    def __call__(self, text, speaker_id: int = 1):
        audio_data = self.model.synth_audio(text, speaker_id=1)
        return to_wav(audio_data)
