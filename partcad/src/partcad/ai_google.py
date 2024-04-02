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

import google.generativeai as google_genai

from . import logging as pc_logging
from .user_config import user_config

lock = threading.Lock()
GOOGLE_API_KEY = None


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
            # raise Exception(error)
            return False

    return True


class AiGoogle:
    def create_content_google(
        self,
        model: str,
        prompt: str,
        image_filenames: list[str] = [],
    ):
        if not google_once():
            return None

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

        client = google_genai.GenerativeModel(model)
        response = client.generate_content(contents)
        if response is None:
            error = "%s: Failed to generate content" % self.name
            pc_logging.error(error)
            # raise Exception(error)
            return None

        try:
            product = response.text

            # Remove code blocks
            product = "\n".join(
                list(
                    filter(
                        lambda l: False if l.startswith("```") else True,
                        product.split("\n"),
                    )
                )
            )

            return product
        except Exception as e:
            pc_logging.exception(e)
            return None
