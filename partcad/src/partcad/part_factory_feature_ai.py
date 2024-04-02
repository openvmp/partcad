#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-03-23
#
# Licensed under Apache License, Version 2.0.
#

import os

from .ai import Ai
from . import logging as pc_logging


class PartFactoryFeatureAi(Ai):
    script_type: str
    prompt_suffix: str

    def __init__(self, part_config, script_type, prompt_suffix=""):
        self.script_type = script_type
        self.prompt_suffix = prompt_suffix

        if not "prompt" in part_config or part_config["prompt"] is None:
            error = "%s: Prompt is not set" % part_config["name"]
            pc_logging.error(error)
            raise Exception(error)
        if not "model" in part_config or part_config["model"] is None:
            warning = "%s: Model is not set" % part_config["name"]
            pc_logging.warning(warning)
            part_config["model"] = "gemini-pro"

    def on_init_ai(self):
        if (
            not os.path.exists(self.part_config["path"])
            or os.path.getsize(self.part_config["path"]) == 0
        ):
            self.create_file()

    def generate(self, part):
        part.invalidate()
        self.create_file()

    def create_file(self):
        prompt = """
        Generate a %s to define a 3D model of a part using the following prompt:
        %s
        """ % (
            self.script_type,
            self.part_config["prompt"],
        )

        if "properties" in self.part_config:
            properties = "\n".join(
                [
                    "  %s: %s" % (k, v)
                    for k, v in self.part_config["properties"].items()
                ]
            )
            prompt += (
                """
                Use the following properties to generate the model:
                %s
                """
                % properties
            )

        prompt += """
            %s
            Produce the %s only without any supplementary text.
            """ % (
            self.prompt_suffix,
            self.script_type,
        )

        content = self.generate_content(
            "Gen", self.project.name, self.name, prompt, self.part_config
        )
        if not content is None:
            f = open(self.part_config["path"], "w")
            f.write(content)
            f.close()
