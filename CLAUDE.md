# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VirtuPy is a virtual avatar chat application that combines a Live2D character with AI-powered conversation and text-to-speech. Users chat via WebSocket, the backend generates responses using OpenAI-compatible APIs, converts them to speech with Silero TTS, and sends expression changes to animate the Live2D model.

## Development Commands

```bash
# Install dependencies (uses uv package manager)
uv sync

# Run the FastAPI server
uv run uvicorn run:app --reload --host 0.0.0.0 --port 5000

# Validate code (always run before committing)
make validate
```

Validation includes:
- Python: isort, black, flake8, mypy
- HTML: html-validate (via npx)
- JavaScript: eslint (via npx)

## Architecture

**Backend (Python/FastAPI):**
- `run.py` - FastAPI application with WebSocket endpoint at `/ws`, serves the frontend from `gui/`
- `virtupy/openai_wrapper.py` - OpenAI API wrapper with retry logic, uses `OPENAI_API_KEY` and `OPENAI_BASE_URL` env vars
- `virtupy/silero_tts.py` - Text-to-speech using Silero models (loaded at startup via lifespan)

**Frontend (gui/):**
- `index.html` - Bootstrap UI with chat widget and expression selector
- `index.js` - Pixi.js + pixi-live2d-display for Live2D rendering, WebSocket communication

**WebSocket Flow:**
1. Client sends text message
2. Server calls `openai_completion()` for response
3. Server calls `choose_expression()` to determine avatar emotion
4. Server sends JSON `{message, expression}` followed by TTS audio bytes
5. Frontend updates chat, sets expression, and plays audio via `model.speak()`

## Code Style

- Avoid obvious comments. Only add comments for genuinely complex logic.

## Environment Variables

Set in `.env`:
- `OPENAI_API_KEY` - API key for OpenAI-compatible service
- `OPENAI_BASE_URL` - Base URL (allows using alternative providers)
