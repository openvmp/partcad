#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-03-23
#
# Licensed under Apache License, Version 2.0.
#

import mimetypes
from pathlib import Path
import threading
import time
from typing import Any

import google.generativeai as google_genai
import google.api_core.exceptions

from . import logging as pc_logging
from .user_config import user_config

lock = threading.Lock()
GOOGLE_API_KEY = None

model_tokens = {
    "gemini-pro": 32600,
    "gemini-pro-vision": 16300,
}


def google_once():
    global GOOGLE_API_KEY

    with lock:
        latest_key = user_config.google_api_key
        if latest_key != GOOGLE_API_KEY:
            GOOGLE_API_KEY = latest_key
            if not GOOGLE_API_KEY is None:
                google_genai.configure(api_key=GOOGLE_API_KEY)
                return True

        if GOOGLE_API_KEY is None:
            error = "Google API key is not set"
            pc_logging.error(error)
            return False

    return True


class AiGoogle:
    def generate_google(
        self,
        model: str,
        prompt: str,
        image_filenames: list[str] = [],
        config: dict[str, Any] = {},
        options_num: int = 1,
    ):
        if not google_once():
            return None

        if "tokens" in config:
            tokens = config["tokens"]
        else:
            tokens = model_tokens[model]

        images = list(
            map(
                lambda f: {
                    "mime_type": mimetypes.guess_type(f, False)[0],
                    "data": Path(f).read_bytes(),
                },
                image_filenames,
            )
        )
        contents = [prompt, *images]

        client = google_genai.GenerativeModel(
            model,
            generation_config={
                # "candidate_count": options_num,
                "max_output_tokens": tokens,
                # "temperature": 0.97,
            },
        )
        candidates = []
        for _ in range(options_num):
            retry = True
            while retry == True:
                retry = False
                try:
                    response = client.generate_content(
                        contents,
                    )
                except google.api_core.exceptions.ResourceExhausted as e:
                    pc_logging.exception(e)
                    retry = True
                    time.sleep(60)
                except google.api_core.exceptions.InternalServerError as e:
                    pc_logging.exception(e)
                    retry = True
                    time.sleep(1)

            if response is None:
                error = "%s: Failed to generate content" % self.name
                pc_logging.error(error)
                continue
            candidates.extend(response.candidates)

        products = []
        try:
            for candidate in candidates:
                product = ""
                for part in candidate.content.parts:
                    if "text" in part:
                        product += part.text + "\n"

                products.append(product)
        except Exception as e:
            pc_logging.exception(e)

        return products
