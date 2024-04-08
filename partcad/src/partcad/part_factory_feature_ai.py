#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-03-23
#
# Licensed under Apache License, Version 2.0.
#

import asyncio

import copy
import os
import tempfile
import threading

from .ai import Ai
from . import logging as pc_logging
from . import sync_threads as pc_thread
from .utils import total_size

NUM_ALTERNATIVES_GEOMETRIC_MODELING = 3
NUM_ALTERNATIVES_MODEL_GENERATION = 3


class PartFactoryFeatureAi(Ai):
    """Used by all part factories that generate parts with GenAI."""

    part_type: str
    script_type: str
    prompt_suffix: str

    def __init__(self, part_config, part_type, script_type, prompt_suffix=""):
        self.part_type = part_type
        self.script_type = script_type
        self.prompt_suffix = prompt_suffix

        prompt = part_config.get("desc", None)
        if prompt is None:
            error = "%s: Prompt is not set" % part_config["name"]
            pc_logging.error(error)
            raise Exception(error)

        self.ai_config = copy.deepcopy(part_config)
        if not "numGeometricModeling" in self.ai_config:
            self.ai_config["numGeometricModeling"] = (
                NUM_ALTERNATIVES_GEOMETRIC_MODELING
            )
        if not "numModelGeneration" in self.ai_config:
            self.ai_config["numModelGeneration"] = (
                NUM_ALTERNATIVES_MODEL_GENERATION
            )
        if not "tokens" in self.ai_config:
            self.ai_config["tokens"] = 2000

    def on_init_ai(self):
        """This method must be executed at the very end of the part factory
        constructor to finalize the AI initialization. At the time of the call
        self.part and self.instantiate must be already defined."""
        self.part.generate = lambda: self._create_file()

        # If uncommented out, this makes the package initialization
        # unaccceptably slow
        # if (
        #     not os.path.exists(self.part_config["path"])
        #     or os.path.getsize(self.part_config["path"]) == 0
        # ):
        #     self._create_file()
        self.instantiate_orig = self.instantiate
        self.instantiate = self._instantiate_ai

    async def _instantiate_ai(self, part):
        """This is a wrapper for the instantiate method that ensures that
        the part is (re)generated before the instantiation."""
        if (
            not os.path.exists(self.part_config["path"])
            or os.path.getsize(self.part_config["path"]) == 0
        ):
            self._create_file()

        return await self.instantiate_orig(part)

    def _create_file(self):
        """This method is called to (re)generate the part."""

        # Geometric modeling
        modeling_options = []

        # def modeling_task():
        #     modeling_options.extend(self._geometric_modeling())
        # threads = []
        # for _ in range(NUM_ALTERNATIVES_GEOMETRIC_MODELING):
        #     thread = threading.Thread(target=modeling_task)
        #     thread.start()
        #     threads.append(thread)
        # for thread in threads:
        #     thread.join()

        while len(modeling_options) < self.ai_config["numGeometricModeling"]:
            modeling_options.extend(self._geometric_modeling())
            pc_logging.info(
                "Generated %d geometric modeling candidates"
                % len(modeling_options)
            )

        # For each remaining geometric modeling option,
        # generate a model and render an image
        script_candidates = []
        candidate_id = 0
        for modeling_option_idx, modeling_option in enumerate(modeling_options):
            pc_logging.debug(
                "Generated the geometric modeling candidate %d: %s"
                % (modeling_option_idx, modeling_option)
            )

            # Generate the models using the required language
            scripts = self._generate_script(modeling_option)

            for script in scripts:
                pc_logging.debug(
                    "Generated the script candidate %d: %s"
                    % (candidate_id, script)
                )

                # Render an image of the model
                image_filename = self._render_image(script, candidate_id)

                # Check if the model was valid
                if image_filename is not None:
                    # Record the valid model and the image
                    script_candidates.append((image_filename, script))

                candidate_id += 1

            pc_logging.info(
                "So far %d valid script candidates" % len(script_candidates)
            )

        if len(script_candidates) == 0:
            pc_logging.error(
                "No valid script generated. Try changing the prompt."
            )
            return

        if len(script_candidates) == 1:
            script = script_candidates[0][1]
        else:
            # Compare the images and select the best one
            script = self.select_best_image(script_candidates)

        if not script is None:
            f = open(self.part_config["path"], "w")
            f.write(script)
            f.close()

    def _geometric_modeling(self):
        """This method generates geometric modeling options for the part."""

        prompt = (
            """You are an engineer performing geometric modeling of mechanical parts.
Given a short verbal description of a part,
you are creating a detailed description of the geometric shapes
required to reproduce that part.
Create a detailed listing of all geometric shapes and how they are
located against each other
(including dimensions, distances and offset in millimeters,
and angles in degrees),
to reproduce the part with the following description:
%s
"""
            % self.ai_config["desc"]
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

The part is further described by the following properties:
%s
"""
                % properties
            )

        image_filenames = self.ai_config.get("images", [])
        if len(image_filenames) > 0:
            prompt += """
            
The part is further described by the attached images.
"""

        options = self.generate(
            "Geometric",
            self.project.name,
            self.name,
            prompt,
            self.ai_config,
            self.ai_config[
                "numGeometricModeling"
            ],  # NUM_ALTERNATIVES_GEOMETRIC_MODELING,
            image_filenames=image_filenames,
        )
        return options

    def _generate_script(self, geometric_modeling):
        """This method generates a script given specific geometric modeling."""

        prompt = """Generate a %s to define a 3D model of a part defined by
the following geometric modeling:
        %s
        """ % (
            self.script_type,
            geometric_modeling,
        )

        image_filenames = self.ai_config.get("images", [])
        if len(image_filenames) > 0:
            prompt += """
            
The part is further described by the attached images.
"""

        prompt += """%s

IMPORTANT: Output the %s itself and do not add any text or comments before or after it.
""" % (
            self.prompt_suffix,
            self.script_type,
        )

        scripts = self.generate(
            "Script",
            self.project.name,
            self.name,
            prompt,
            self.ai_config,
            self.ai_config["numModelGeneration"],
            image_filenames=image_filenames,
        )

        # Sanitize the output to remove the decorations
        scripts = list(map(lambda s: self._sanitize_script(s), scripts))

        return scripts

    def _sanitize_script(self, script):
        """Cleans up the GenAI output to keep the code only."""

        # Remove code blocks
        script = "\n".join(
            list(
                filter(
                    lambda l: (
                        False
                        if l.startswith("```") or l.startswith(" ```")
                        else True
                    ),
                    script.split("\n"),
                )
            )
        )

        return script

    def _render_image(self, script, candidate_id):
        """This method ensures the validity of a script candidate by attempting to render it."""

        source_path = tempfile.mktemp(suffix=self.extension)
        with open(source_path, "w") as f:
            f.write(script)
            f.close()
        pc_logging.debug("Generated script: %s" % source_path)

        output_path = tempfile.mktemp(suffix=".png")
        pc_logging.debug("Attempting to render: %s" % output_path)

        # Create an ephemeral part for the given script candidate
        part = self._create_part(
            {
                "name": self.name + "_candidate_" + str(candidate_id),
                # "path": source_path, # TODO(clairbee): doesn't this work? why?
                "type": self.part_type,
                "mute": True,  # Suppress errors
            }
        )
        # Since this is an ephemeral part, certain things need to be tweaked
        part.instantiate = self.instantiate_orig  # Remove the AI wrapper
        part.path = source_path  # Set the path to the temporary script file
        pc_logging.debug("Part created: %.2f KB" % (total_size(part) / 1024.0))

        def render(part):
            try:
                coro = part.get_shape()
                with pc_logging.Action(
                    "Instantiate", part.project_name, part.name
                ):
                    shape = asyncio.run(coro)
                if not shape is None:
                    part.render_png(self.ctx, None, output_path)
            except Exception as e:
                part.error("Failed to render the image: %s" % e)

        try:
            # Given we don't know whether the current thread is already
            # running an event loop or not, we need to create a new thread
            t = threading.Thread(target=render, args=[part])
            t.start()
            t.join()
        except Exception as e:
            part.error("Failed to render the image: %s" % e)

        if len(part.errors) > 0:
            pc_logging.debug(
                "There were errors while attemtping to render the image"
            )
            pc_logging.debug("%s" % part.errors)

        os.unlink(source_path)
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            pc_logging.info(
                "Script candidate %d: failed to render the image" % candidate_id
            )
            return None
        pc_logging.info(
            "Script candidate %d: successfully rendered the image"
            % candidate_id
        )
        return output_path

    def select_best_image(self, script_candidates):
        """Iterate over script_candidates and compare images.
        Each script candidate is [<image_filename>, <script>]."""

        if len(script_candidates) == 0:
            return None

        image_filenames = list(map(lambda c: c[0], script_candidates))

        prompt = (
            """
From the attached images, select the image that is the best fit
for the following description:
%s

Respond with the numeric index (starting with 1) of the best fit image.
No other text is acceptable.
Just the number.
"""
            % self.ai_config["desc"]
        )

        # Ask AI to compare the images
        responses = self.generate(
            "Compare",
            self.project.name,
            self.name,
            prompt,
            self.ai_config,
            1,
            image_filenames=image_filenames,
        )

        pc_logging.debug("Image comparison responses: %s" % responses)

        # Parse the response to get the number out
        for response in responses:
            words = response.split(" ")
            words = list(filter(lambda w: w.strip().isnumeric(), words))
            if len(words) == 1:
                idx = int(words[0])
                if idx > 0 and idx <= len(script_candidates):
                    pc_logging.info("Selected the best fit image: %d" % idx)
                    return script_candidates[idx - 1][1]

        return script_candidates[0][1]
