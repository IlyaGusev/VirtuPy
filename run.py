import random
import asyncio
import json
import time
import io
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from virtupy.openai_wrapper import openai_completion
from virtupy.silero_tts import SileroTTS

models = {}

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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    messages = [{"role": "system", "content": "Ты общительная виртуальная девушка"}]
    try:
        while True:
            text = await websocket.receive_text()
            messages.append({"role": "user", "content": text})
            answer = openai_completion(messages)
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
