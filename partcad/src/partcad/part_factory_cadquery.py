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
from cq_serialize import (
    register as register_cq_helper,
)  # import this one for `pickle` to use


class PartFactoryCadquery(pfp.PartFactoryPython):
    def __init__(self, ctx, project, part_config):
        with pc_logging.Action("InitCadQuery", project.name, part_config["name"]):
            super().__init__(ctx, project, part_config)
            # Complement the config object here if necessary
            self._create(part_config)

    def instantiate(self, part):
        with pc_logging.Action("CadQuery", part.project_name, part.name):
            wrapper_path = wrapper.get("cadquery.py")

            request = {"build_parameters": {}}
            if "parameters" in self.part_config:
                for param_name, param in self.part_config["parameters"].items():
                    request["build_parameters"][param_name] = param["default"]

            picklestring = pickle.dumps(request)
            request_serialized = base64.b64encode(picklestring).decode()

            self.runtime.ensure("cadquery")
            response_serialized, errors = self.runtime.run(
                [
                    wrapper_path,
                    os.path.abspath(self.path),
                    os.path.abspath(self.project.config_dir),
                ],
                request_serialized,
            )
            sys.stderr.write(errors)

            response = base64.b64decode(response_serialized)
            result = pickle.loads(response)

            if not result["success"]:
                pc_logging.error(result["exception"])
                raise Exception(result["exception"])

            self.ctx.stats_parts_instantiated += 1

            return result["shape"]
