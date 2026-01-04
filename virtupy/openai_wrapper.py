import os
import copy
import logging
import time
import pathlib
from dataclasses import dataclass
from typing import Optional, Sequence
from multiprocessing.pool import ThreadPool

from openai import OpenAI
from jinja2 import Template
from dotenv import load_dotenv

load_dotenv()

OPENAI_MODELS = ("gpt-4o-mini",)

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
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_SLEEP_TIME = 20
CLIENT = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

def openai_completion(
    messages,
    decoding_args: OpenAIDecodingArguments = DEFAULT_ARGS,
    model_name: str = DEFAULT_MODEL,
    sleep_time: int = DEFAULT_SLEEP_TIME
):
    decoding_args = copy.deepcopy(decoding_args)
    assert decoding_args.n == 1
    while True:
        try:
            completions = CLIENT.chat.completions.create(
                messages=messages,
                model=model_name,
                **decoding_args.__dict__
            )
            break
        except Exception as e:
            logging.warning(f"OpenAIError: {e}.")
            if "Please reduce" in str(e):
                decoding_args.max_tokens = int(decoding_args.max_tokens * 0.8)
                logging.warning(f"Reducing target length to {decoding_args.max_tokens}, Retrying...")
            else:
                logging.warning("Hit request rate limit; retrying...")
                time.sleep(sleep_time)
    return completions.choices[0].message.content
