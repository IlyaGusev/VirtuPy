import io
from typing import Any

import numpy as np
import torch
from scipy.io import wavfile  # type: ignore[import-untyped]

SILERO_VOICES = {
    "ru": {"speakers": ["aidar", "baya", "kseniya", "xenia", "eugene"], "model": "v3_1_ru"},
    "en": {
        "speakers": [
            "en_0",
            "en_1",
            "en_2",
            "en_3",
            "en_4",
            "en_5",
            "en_6",
            "en_7",
            "en_8",
            "en_9",
            "en_10",
            "en_11",
            "en_12",
            "en_13",
            "en_14",
            "en_15",
            "en_16",
            "en_17",
            "en_18",
            "en_19",
            "en_20",
            "en_21",
            "en_22",
            "en_23",
            "en_24",
            "en_25",
            "en_26",
            "en_27",
            "en_28",
            "en_29",
            "en_30",
            "en_31",
            "en_32",
            "en_33",
            "en_34",
            "en_35",
            "en_36",
            "en_37",
            "en_38",
            "en_39",
            "en_40",
            "en_41",
            "en_42",
            "en_43",
            "en_44",
            "en_45",
            "en_46",
            "en_47",
            "en_48",
            "en_49",
            "en_50",
            "en_51",
            "en_52",
            "en_53",
            "en_54",
            "en_55",
            "en_56",
            "en_57",
            "en_58",
            "en_59",
            "en_60",
            "en_61",
            "en_62",
            "en_63",
            "en_64",
            "en_65",
            "en_66",
            "en_67",
            "en_68",
            "en_69",
            "en_70",
            "en_71",
            "en_72",
            "en_73",
            "en_74",
            "en_75",
            "en_76",
            "en_77",
            "en_78",
            "en_79",
            "en_80",
            "en_81",
            "en_82",
            "en_83",
            "en_84",
            "en_85",
            "en_86",
            "en_87",
            "en_88",
            "en_89",
            "en_90",
            "en_91",
            "en_92",
            "en_93",
            "en_94",
            "en_95",
            "en_96",
            "en_97",
            "en_98",
            "en_99",
            "en_100",
            "en_101",
            "en_102",
            "en_103",
            "en_104",
            "en_105",
            "en_106",
            "en_107",
            "en_108",
            "en_109",
            "en_110",
            "en_111",
            "en_112",
            "en_113",
            "en_114",
            "en_115",
            "en_116",
            "en_117",
        ],
        "model": "v3_en",
    },
    "de": {
        "speakers": ["bernd_ungerer", "eva_k", "friedrich", "hokuspokus", "karlsson"],
        "model": "v3_de",
    },
    "es": {"speakers": ["es_0", "es_1", "es_2"], "model": "v3_es"},
    "fr": {"speakers": ["fr_0", "fr_1", "fr_2", "fr_3", "fr_4", "fr_5"], "model": "v3_fr"},
}


DEFAULT_LANGUAGE = "ru"
DEFAULT_SPEAKER = "baya"


class SileroTTS:
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.models: dict[str, Any] = {}

    def _load_model(self, language: str):
        if language not in self.models:
            model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language=language,
                speaker=SILERO_VOICES[language]["model"],
            )
            self.models[language] = model
        return self.models[language]

    @staticmethod
    def get_available_voices() -> dict:
        return {lang: data["speakers"] for lang, data in SILERO_VOICES.items()}

    def __call__(
        self, text: str, language: str = DEFAULT_LANGUAGE, speaker: str = DEFAULT_SPEAKER
    ) -> bytes:
        model = self._load_model(language)
        audio = model.apply_tts(text=text, speaker=speaker, sample_rate=self.sample_rate)
        audio_np = (audio.numpy() * 32767).astype(np.int16)
        buffer = io.BytesIO()
        wavfile.write(buffer, self.sample_rate, audio_np)
        buffer.seek(0)
        return buffer.read()
