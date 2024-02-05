import random
import asyncio
import json
import time

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        await websocket.send_text(json.dumps({"expression": random.randint(0, 5)}))
        await asyncio.sleep(5)

app.mount("/", StaticFiles(directory="gui", html=True), name="gui")
