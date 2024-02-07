import random
import asyncio
import json
import time
import io
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from virtupy.openai_wrapper import openai_completion
from virtupy.tts import TTS

models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    models["tts"] = TTS()
    yield
    models.clear()


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    messages = [{"role": "system", "content": "Ты общительная виртуальная девушка"}]
    try:
        while True:
            text = await websocket.receive_text()
            messages.append({"role": "user", "content": text})
            answer = openai_completion(messages)
            await websocket.send_text(json.dumps({"message": answer}))
            messages.append({"role": "assistant", "content": answer})
            audio = models["tts"](answer)
            await websocket.send_bytes(audio)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error: {e}")


app.mount("/", StaticFiles(directory="gui", html=True), name="gui")


#await websocket.send_text(json.dumps({"expression": random.randint(0, 5)}))
