#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-03-23
#
# Licensed under Apache License, Version 2.0.
#

from .ai_google import AiGoogle
from .ai_openai import AiOpenAI

from . import logging as pc_logging
from .user_config import user_config


models = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gemini-pro",
    "gemini-pro-vision",
]


class Ai(AiGoogle, AiOpenAI):
    def generate_content(
        self,
        action: str,
        package: str,
        item: str,
        prompt: str,
        config: dict[str, str],
    ):
        with pc_logging.Action("Ai" + action, package, item):
            # Normalize the list of images provided if any
            if "images" in config and config["images"] is not None:
                image_filenames = config["images"]
            else:
                image_filenames = []

            # Determine the model to use
            if "model" in config and config["model"] is not None:
                model = config["model"]
            else:
                # Guess the model based on the API key and the content
                if user_config.openai_api_key is None:
                    if len(image_filenames) > 0:
                        model = "gemini-pro-vision"
                    else:
                        model = "gemini-pro"
                else:
                    if len(image_filenames) > 0:
                        model = "gpt-4"
                    else:
                        model = "gpt-3.5-turbo"

            if model.startswith("gemini"):
                content = self.create_content_google(
                    model,
                    prompt,
                    image_filenames,
                )

            elif model.startswith("gpt"):
                if "tokens" in config:
                    tokens = config["tokens"]
                else:
                    tokens = None
                if "top_p" in config:
                    top_p = config["top_p"]
                else:
                    top_p = None
                content = self.create_content_openai(
                    model,
                    prompt,
                    image_filenames,
                    tokens,
                    top_p,
                )

            return content
