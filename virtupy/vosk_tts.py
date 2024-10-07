from vosk_tts import Synth, Model

from virtupy.utils import to_wav

class VoskTTS:
    def __init__(self, model_name: str = "vosk-model-tts-ru-0.6-multi"):
        self.model = Synth(Model(model_name=model_name))

    def __call__(self, text, speaker_id: int = 1):
        audio_data = self.model.synth_audio(text, speaker_id=1)
        return to_wav(audio_data)
