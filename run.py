from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/", StaticFiles(directory="gui", html=True), name="gui")
