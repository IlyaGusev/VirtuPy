import json
import re
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from virtupy.openai_wrapper import AVAILABLE_LLMS, DEFAULT_MODEL, openai_completion_stream
from virtupy.silero_tts import DEFAULT_LANGUAGE, DEFAULT_SPEAKER, SILERO_VOICES, SileroTTS

# Regex patterns
EXPRESSION_PATTERN = re.compile(r'\[EXPRESSION:\s*(\w+)\]')
EXPRESSION_TAG_PATTERN = re.compile(r'\[EXPRESSION:\s*\w+\]\s*')
SENTENCE_ENDINGS = re.compile(r'[.!?。！？]+')

# TTS batching settings
MIN_BATCH_CHARS = 20
MAX_BATCH_CHARS = 300

SYSTEM_PROMPT_TEMPLATE = """Ты общительная виртуальная девушка.

ПРАВИЛО: Ответ ВСЕГДА начинается с тега эмоции. Формат: [EXPRESSION: эмоция] текст ответа
Используй ТОЛЬКО ОДИН тег в самом начале. Не используй теги в середине или конце текста.
Доступные эмоции: {expressions}

Пример:
[EXPRESSION: {example_expression}] Привет! Рада тебя видеть!"""

DEFAULT_LIVE2D_MODEL = "haru"

LIVE2D_MODELS = {
    "haru": {
        "name": "Haru",
        "url": "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/haru/haru_greeter_t03.model3.json",
        "expressions": {
            "smiling": "f00",
            "sad": "f03",
            "happy": "f04",
            "scared": "f05",
            "shy": "f06",
            "tired": "f07",
            "angry": "f02",
        },
    },
    "shizuku": {
        "name": "Shizuku",
        "url": "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/shizuku/shizuku.model.json",
        "expressions": {"smiling": "f01", "sad": "f02", "angry": "f03", "happy": "f04"},
    },
    "natori": {
        "name": "Natori",
        "url": "https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@master/Samples/Resources/Natori/Natori.model3.json",
        "expressions": {
            "smiling": "Smile",
            "sad": "Sad",
            "happy": "Smile",
            "scared": "Surprised",
            "shy": "Blushing",
            "tired": "Normal",
            "angry": "Angry",
        },
    },
    "mao": {
        "name": "Mao",
        "url": "https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@master/Samples/Resources/Mao/Mao.model3.json",
        "expressions": {
            "smiling": "exp_01",
            "happy": "exp_02",
            "proud": "exp_03",
            "excited": "exp_04",
            "sad": "exp_05",
            "blushing": "exp_06",
            "scared": "exp_07",
            "angry": "exp_08",
        },
    },
    "hiyori": {
        "name": "Hiyori",
        "url": "https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@master/Samples/Resources/Hiyori/Hiyori.model3.json",
        "expressions": {},
    },
    "mark": {
        "name": "Mark",
        "url": "https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@master/Samples/Resources/Mark/Mark.model3.json",
        "expressions": {},
    },
    "rice": {
        "name": "Rice",
        "url": "https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@master/Samples/Resources/Rice/Rice.model3.json",
        "expressions": {},
    },
}

models = {}


def get_available_expressions(live2d_model: str) -> list[str]:
    """Get expression names available for a Live2D model."""
    model_data = LIVE2D_MODELS.get(live2d_model, {})
    return list(model_data.get("expressions", {}).keys())


def build_system_prompt(live2d_model: str) -> str:
    """Build system prompt with expressions available for given model."""
    expressions = get_available_expressions(live2d_model)
    if not expressions:
        expressions = ["happy"]  # Fallback if model has no expressions
    return SYSTEM_PROMPT_TEMPLATE.format(
        expressions=", ".join(expressions),
        example_expression=expressions[0] if expressions else "happy",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    models["tts"] = SileroTTS()
    yield
    models.clear()


app = FastAPI(lifespan=lifespan)


def parse_expression(text: str, live2d_model: str) -> str | None:
    match = EXPRESSION_PATTERN.search(text)
    if match:
        expr = match.group(1).lower()
        available = get_available_expressions(live2d_model)
        if expr in available:
            return expr
    return None


def remove_expression_tag(text: str) -> str:
    return EXPRESSION_TAG_PATTERN.sub("", text)


def find_batch_cutoff(text: str) -> int | None:
    """Find a good cutoff point for text batching at sentence boundaries."""
    matches = list(SENTENCE_ENDINGS.finditer(text))
    if not matches:
        return None

    cutoff = None
    for match in matches:
        if match.end() >= MIN_BATCH_CHARS:
            if match.end() >= MAX_BATCH_CHARS:
                return match.end()
            cutoff = match.end()
    return cutoff


@app.get("/api/models")
async def get_models():
    return JSONResponse(content=LIVE2D_MODELS)


@app.get("/api/voices")
async def get_voices():
    return JSONResponse(
        content={
            "available": SileroTTS.get_available_voices(),
            "default": {"language": DEFAULT_LANGUAGE, "speaker": DEFAULT_SPEAKER},
        }
    )


@app.get("/api/llm")
async def get_llm():
    return JSONResponse(content={"available": AVAILABLE_LLMS, "default": DEFAULT_MODEL})


def has_speakable_text(text: str) -> bool:
    return any(c.isalpha() for c in text)


async def send_text_with_audio(websocket: WebSocket, text: str, language: str, speaker: str):
    await websocket.send_text(json.dumps({"text": text}))
    if has_speakable_text(text):
        audio = models["tts"](text, language, speaker)
        await websocket.send_bytes(audio)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    messages: list[dict[str, str]] = []
    live2d_model = DEFAULT_LIVE2D_MODEL
    llm = DEFAULT_MODEL
    tts_language = DEFAULT_LANGUAGE
    tts_speaker = DEFAULT_SPEAKER

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
                if "model" in data:
                    if data["model"] in LIVE2D_MODELS:
                        live2d_model = data["model"]
                    continue
                if "llm" in data:
                    if data["llm"] in AVAILABLE_LLMS:
                        llm = data["llm"]
                    continue
                if "voice" in data:
                    lang = data["voice"].get("language")
                    spk = data["voice"].get("speaker")
                    if lang in SILERO_VOICES and spk in SILERO_VOICES[lang]["speakers"]:
                        tts_language = lang
                        tts_speaker = spk
                    continue
                text = data.get("text", "")
            except json.JSONDecodeError:
                text = raw

            if not text:
                continue

            system_prompt = build_system_prompt(live2d_model)
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] = system_prompt
            else:
                messages.insert(0, {"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": text})

            full_response = ""
            expression_sent = False
            text_buffer = ""

            for chunk in openai_completion_stream(messages, model_name=llm):
                full_response += chunk
                text_buffer += chunk

                if not expression_sent:
                    expression = parse_expression(full_response, live2d_model)
                    if expression:
                        await websocket.send_text(json.dumps({"expression": expression}))
                        expression_sent = True
                        text_buffer = remove_expression_tag(text_buffer)

                if expression_sent and len(text_buffer) >= MIN_BATCH_CHARS:
                    cutoff = find_batch_cutoff(text_buffer)
                    if cutoff:
                        batch_text = remove_expression_tag(text_buffer[:cutoff]).strip()
                        text_buffer = text_buffer[cutoff:].lstrip()
                        if batch_text:
                            await send_text_with_audio(websocket, batch_text + " ", tts_language, tts_speaker)

            remaining = remove_expression_tag(text_buffer).strip()
            if remaining:
                await send_text_with_audio(websocket, remaining, tts_language, tts_speaker)

            await websocket.send_text(json.dumps({"done": True}))

            clean_response = remove_expression_tag(full_response)
            messages.append({"role": "assistant", "content": clean_response})

    except WebSocketDisconnect:
        pass
    except Exception:
        traceback.print_exc()


app.mount("/", StaticFiles(directory="gui", html=True), name="gui")
