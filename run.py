import random
import asyncio
import json
import time
import io
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from virtupy.openai_wrapper import openai_completion, AVAILABLE_LLMS, DEFAULT_MODEL
from virtupy.silero_tts import SileroTTS

models = {}
current_llm = DEFAULT_MODEL

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
            "angry": "f02"
        }
    },
    "shizuku": {
        "name": "Shizuku",
        "url": "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/shizuku/shizuku.model.json",
        "expressions": {
            "smiling": "f01",
            "sad": "f02",
            "angry": "f03",
            "happy": "f04"
        }
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
            "angry": "Angry"
        }
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
            "angry": "exp_08"
        }
    },
    "hiyori": {
        "name": "Hiyori",
        "url": "https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@master/Samples/Resources/Hiyori/Hiyori.model3.json",
        "expressions": {}
    },
    "mark": {
        "name": "Mark",
        "url": "https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@master/Samples/Resources/Mark/Mark.model3.json",
        "expressions": {}
    },
    "rice": {
        "name": "Rice",
        "url": "https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@master/Samples/Resources/Rice/Rice.model3.json",
        "expressions": {}
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    models["tts"] = SileroTTS()
    yield
    models.clear()


app = FastAPI(lifespan=lifespan)


EMOTE_PROMPT = """Based on the following conversation, choose one of the expressions from a list.

Conversation:
{conversation}

Possible expressions:
{expressions}

Your choice:
"""

def choose_expression(messages):
    expressions = ["smiling", "sad", "happy", "scared", "shy", "tired", "angry"]
    conversation = "\n".join([m["role"] + ": " + m["content"] for m in messages])
    content = EMOTE_PROMPT.format(conversation=conversation, expressions=expressions)
    messages = [{"role": "user", "content": content}]
    answer = openai_completion(messages)
    for expression in expressions:
        if expression in answer.lower():
            return expression
    return "smiling"


@app.get("/api/models")
async def get_models():
    return JSONResponse(content=LIVE2D_MODELS)


@app.get("/api/voices")
async def get_voices():
    return JSONResponse(content={
        "available": SileroTTS.get_available_voices(),
        "current": models["tts"].get_current_voice()
    })


@app.post("/api/voice")
async def set_voice(language: str, speaker: str):
    try:
        models["tts"].set_voice(language, speaker)
        return JSONResponse(content={"success": True, "voice": models["tts"].get_current_voice()})
    except ValueError as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=400)


@app.get("/api/llm")
async def get_llm():
    return JSONResponse(content={"available": AVAILABLE_LLMS, "current": current_llm})


@app.post("/api/llm")
async def set_llm(model: str):
    global current_llm
    if model not in AVAILABLE_LLMS:
        return JSONResponse(content={"success": False, "error": "Invalid model"}, status_code=400)
    current_llm = model
    return JSONResponse(content={"success": True, "current": current_llm})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    messages = [{"role": "system", "content": "Ты общительная виртуальная девушка"}]
    try:
        while True:
            text = await websocket.receive_text()
            messages.append({"role": "user", "content": text})
            answer = openai_completion(messages, model_name=current_llm)
            messages.append({"role": "assistant", "content": answer})
            expression = choose_expression(messages)
            await websocket.send_text(json.dumps({"message": answer, "expression": expression}))
            audio = models["tts"](answer)
            await websocket.send_bytes(audio)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error: {e}")


app.mount("/", StaticFiles(directory="gui", html=True), name="gui")
