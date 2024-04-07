#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-03-23
#
# Licensed under Apache License, Version 2.0.
#

import time

from .ai_google import AiGoogle
from .ai_openai import AiOpenAI

from . import logging as pc_logging
from .user_config import user_config


models = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4-vision-preview",
    "gemini-pro",
    "gemini-pro-vision",
]


class Ai(AiGoogle, AiOpenAI):
    def generate(
        self,
        action: str,
        package: str,
        item: str,
        prompt: str,
        config: dict[str, str],
        num_options: int = 1,
        image_filenames: list[str] = [],
    ):
        with pc_logging.Action("Ai" + action, package, item):
            # Determine the model to use
            if "model" in config and config["model"] is not None:
                model = config["model"]
            else:
                provider = config.get("provider", None)
                if provider is None:
                    if not user_config.openai_api_key is None:
                        provider = "openai"
                    else:
                        provider = "google"

                if provider == "google":
                    if len(image_filenames) > 0:
                        model = "gemini-pro-vision"
                    else:
                        model = "gemini-pro"
                elif provider == "openai":
                    if len(image_filenames) > 0:
                        model = "gpt-4-vision-preview"
                    else:
                        model = "gpt-4"
                else:
                    error = "Provider %s is not supported" % provider
                    pc_logging.error(error)
                    return []

            # Generate the content
            if not model in models:
                error = "Model %s is not supported" % model
                pc_logging.error(error)
                return []

            result = []
            if model.startswith("gemini"):
                try:
                    result = self.generate_google(
                        model,
                        prompt,
                        image_filenames,
                        config,
                        num_options,
                    )
                except Exception as e:
                    pc_logging.error(
                        "Failed to generate with Google: %s" % str(e)
                    )
                    time.sleep(1)  # Safeguard against exceeding quota

            elif model.startswith("gpt"):
                try:
                    result = self.generate_openai(
                        model,
                        prompt,
                        image_filenames,
                        config,
                        num_options,
                    )
                except Exception as e:
                    pc_logging.error(
                        "Failed to generate with OpenAI: %s" % str(e)
                    )
                    time.sleep(1)  # Safeguard against exceeding quota

            else:
                pc_logging.error(
                    "Failed to associate the model %s with the provider" % model
                )

            if result is None:
                return []
            return result
