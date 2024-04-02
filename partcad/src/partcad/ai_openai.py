#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-03-23
#
# Licensed under Apache License, Version 2.0.
#

import base64
import mimetypes
from pathlib import Path
import threading

import openai as openai_genai

from . import logging as pc_logging
from .user_config import user_config

lock = threading.Lock()
OPENAI_API_KEY = None
openai_client = None


def openai_once():
    global OPENAI_API_KEY, openai_client

    with lock:
        latest_key = user_config.openai_api_key
        if latest_key != OPENAI_API_KEY:
            OPENAI_API_KEY = latest_key
            if not OPENAI_API_KEY is None:
                openai_genai.api_key = OPENAI_API_KEY
                openai_client = openai_genai.OpenAI(api_key=OPENAI_API_KEY)
                return True

        if OPENAI_API_KEY is None:
            error = "OpenAI API key is not set"
            pc_logging.error(error)
            # raise Exception(error)
            return False

    return True


class AiOpenAI:
    def create_content_openai(
        self,
        model: str,
        prompt: str,
        image_filenames: list[str] = [],
        tokens: int = None,
        top_p: float = None,
    ):
        if not openai_once():
            return None

        if tokens is None:
            # TODO(clairbee): detect the model's max value
            tokens = 2048

        content = [
            {"type": "text", "text": prompt},
            *list(
                map(
                    lambda f: {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:%s;base64,%s"
                            % (
                                mimetypes.guess_type(f, False)[0],
                                base64.b64encode(Path(f).read_bytes()).decode(),
                            ),
                            "detail": "high",
                        },
                    },
                    image_filenames,
                )
            ),
        ]

        cc = openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a mechanical engineer"},
                {"role": "user", "content": content},
            ],
            stream=False,
            max_tokens=tokens,
            top_p=top_p,
            model=model,
        )

        try:
            script = cc.choices[0].message.content

            # Remove code blocks
            script = "\n".join(
                list(
                    filter(
                        lambda l: False if l.startswith("```") else True,
                        script.split("\n"),
                    )
                )
            )

            return script
        except Exception as e:
            pc_logging.exception(e)
            return None
