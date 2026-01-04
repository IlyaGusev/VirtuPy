import asyncio
import copy
import logging
import os
from dataclasses import dataclass
from typing import AsyncIterator, Optional, Sequence

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

AVAILABLE_LLMS = [
    "deepseek/deepseek-chat-v3-0324",
    "openai/gpt-5-mini",
    "anthropic/claude-haiku-4.5",
]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")


@dataclass
class OpenAIDecodingArguments:
    max_tokens: int = 2560
    temperature: float = 1.0
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    stop: Optional[Sequence[str]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


DEFAULT_ARGS = OpenAIDecodingArguments()
DEFAULT_MODEL = "deepseek/deepseek-chat-v3-0324"
DEFAULT_SLEEP_TIME = 20
CLIENT = AsyncOpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)


async def openai_completion(
    messages,
    decoding_args: OpenAIDecodingArguments = DEFAULT_ARGS,
    model_name: str = DEFAULT_MODEL,
    sleep_time: int = DEFAULT_SLEEP_TIME,
):
    decoding_args = copy.deepcopy(decoding_args)
    assert decoding_args.n == 1
    while True:
        try:
            completions = await CLIENT.chat.completions.create(
                messages=messages, model=model_name, **decoding_args.__dict__
            )
            break
        except Exception as e:
            logging.warning(f"OpenAIError: {e}.")
            if "Please reduce" in str(e):
                decoding_args.max_tokens = int(decoding_args.max_tokens * 0.8)
                logging.warning(
                    f"Reducing target length to {decoding_args.max_tokens}, Retrying..."
                )
            else:
                logging.warning("Hit request rate limit; retrying...")
                await asyncio.sleep(sleep_time)
    return completions.choices[0].message.content


async def openai_completion_stream(
    messages,
    model_name: str = DEFAULT_MODEL,
    sleep_time: int = DEFAULT_SLEEP_TIME,
) -> AsyncIterator[str]:
    while True:
        try:
            stream = await CLIENT.chat.completions.create(
                messages=messages,
                model=model_name,
                stream=True,
                max_tokens=2560,
                temperature=1.0,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            break
        except Exception as e:
            logging.warning(f"OpenAIError: {e}.")
            logging.warning("Hit request rate limit; retrying...")
            await asyncio.sleep(sleep_time)
