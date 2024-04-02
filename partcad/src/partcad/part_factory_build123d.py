#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-01
#
# Licensed under Apache License, Version 2.0.
#

import base64
import os
import pickle
import sys

from . import part_factory_python as pfp
from . import wrapper
from . import logging as pc_logging

sys.path.append(os.path.join(os.path.dirname(__file__), "wrappers"))
from cq_serialize import register as register_cq_helper


class PartFactoryBuild123d(pfp.PartFactoryPython):
    def __init__(self, ctx, source_project, target_project, part_config):
        with pc_logging.Action(
            "InitBuild123d", target_project.name, part_config["name"]
        ):
            super().__init__(ctx, source_project, target_project, part_config)
            # Complement the config object here if necessary
            self._create(part_config)

    async def instantiate(self, part):
        with pc_logging.Action("Build123d", part.project_name, part.name):
            # Finish initialization of PythonRuntime
            # which was too expensive to do in the constructor
            await self.prepare_python()

            # Get the path to the wrapper script
            # which needs to be executed
            wrapper_path = wrapper.get("build123d.py")

            # Build the request
            request = {"build_parameters": {}}

            # Serialize the request
            register_cq_helper()
            picklestring = pickle.dumps(request)
            request_serialized = base64.b64encode(picklestring).decode()

            await self.runtime.ensure("build123d")
            response_serialized, errors = await self.runtime.run(
                [wrapper_path, self.path], request_serialized
            )
            sys.stderr.write(errors)

            response = base64.b64decode(response_serialized)
            register_cq_helper()
            result = pickle.loads(response)

            if not result["success"]:
                pc_logging.error(result["exception"])
                raise Exception(result["exception"])

            self.ctx.stats_parts_instantiated += 1

            return result["shape"]
