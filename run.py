import random
import asyncio
import json
import time
import io

import wave
from vosk_tts import Model, Synth
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from virtupy.openai_wrapper import openai_completion


model = Model(model_name="vosk-model-tts-ru-0.6-multi")
synth = Synth(model)


def tts(text):
    return synth.synth_audio(text, speaker_id=1)


def to_wav(audio, channels=1, sampwidth=2, framerate=22050):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels) 
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.getvalue()


app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            messages = [{"role": "system", "content": "Ты общительная виртуальная девушка"}, {"role": "user", "content": text}]
            answer = openai_completion(messages)
            print(answer)
            audio = tts(answer)
            audio_data = to_wav(audio)
            await websocket.send_bytes(audio_data)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error: {e}")

app.mount("/", StaticFiles(directory="gui", html=True), name="gui")


#await websocket.send_text(json.dumps({"expression": random.randint(0, 5)}))
