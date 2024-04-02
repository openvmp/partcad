#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
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


class PartFactoryCadquery(pfp.PartFactoryPython):
    def __init__(self, ctx, source_project, target_project, part_config):
        with pc_logging.Action(
            "InitCadQuery", target_project.name, part_config["name"]
        ):
            super().__init__(ctx, source_project, target_project, part_config)
            # Complement the config object here if necessary
            self._create(part_config)

    async def instantiate(self, part):
        with pc_logging.Action("CadQuery", part.project_name, part.name):
            # Finish initialization of PythonRuntime
            # which was too expensive to do in the constructor
            await self.prepare_python()

            # Get the path to the wrapper script
            # which needs to be executed
            wrapper_path = wrapper.get("cadquery.py")

            # Build the request
            request = {"build_parameters": {}}
            if "parameters" in self.part_config:
                for param_name, param in self.part_config["parameters"].items():
                    request["build_parameters"][param_name] = param["default"]

            # Serialize the request
            register_cq_helper()
            picklestring = pickle.dumps(request)
            request_serialized = base64.b64encode(picklestring).decode()

            await self.runtime.ensure("cadquery")
            response_serialized, errors = await self.runtime.run(
                [
                    wrapper_path,
                    os.path.abspath(self.path),
                    os.path.abspath(self.project.config_dir),
                ],
                request_serialized,
            )
            sys.stderr.write(errors)

            response = base64.b64decode(response_serialized)
            register_cq_helper()
            result = pickle.loads(response)

            if not result["success"]:
                pc_logging.error("%s: %s" % (self.name, result["exception"]))
                # raise Exception(result["exception"])
                return None

            self.ctx.stats_parts_instantiated += 1

            return result["shape"]
