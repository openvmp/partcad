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

from OCP.TopoDS import (
    TopoDS_Builder,
    TopoDS_Compound,
)

from . import part_factory_python as pfp
from . import wrapper
from . import logging as pc_logging

sys.path.append(os.path.join(os.path.dirname(__file__), "wrappers"))
from cq_serialize import register as register_cq_helper


class PartFactoryCadquery(pfp.PartFactoryPython):
    def __init__(
        self, ctx, source_project, target_project, part_config, can_create=False
    ):
        with pc_logging.Action(
            "InitCadQuery", target_project.name, part_config["name"]
        ):
            super().__init__(
                ctx,
                source_project,
                target_project,
                part_config,
                can_create=can_create,
            )
            # Complement the config object here if necessary
            self._create(part_config)

    async def instantiate(self, part):
        with pc_logging.Action("CadQuery", part.project_name, part.name):
            if not os.path.exists(part.path) or os.path.getsize(part.path) == 0:
                pc_logging.error(
                    "CadQuery script is empty or does not exist: %s" % part.path
                )
                return None

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
            patch = {}
            if "patch" in self.part_config:
                patch.update(self.part_config["patch"])
            request["patch"] = patch

            # Serialize the request
            register_cq_helper()
            picklestring = pickle.dumps(request)
            request_serialized = base64.b64encode(picklestring).decode()

            await self.runtime.ensure("cadquery")
            await self.runtime.ensure("ocp-tessellate")
            cwd = self.project.config_dir
            if self.cwd is not None:
                cwd = os.path.join(self.project.config_dir, self.cwd)
            response_serialized, errors = await self.runtime.run(
                [
                    wrapper_path,
                    os.path.abspath(part.path),
                    os.path.abspath(cwd),
                ],
                request_serialized,
            )
            if len(errors) > 0:
                error_lines = errors.split("\n")
                for error_line in error_lines:
                    part.error("%s: %s" % (part.name, error_line))

            try:
                # pc_logging.error("Response: %s" % response_serialized)
                response = base64.b64decode(response_serialized)
                register_cq_helper()
                result = pickle.loads(response)
            except Exception as e:
                part.error(
                    "Exception while deserializing %s: %s" % (part.name, e)
                )
                return None

            if not result["success"]:
                part.error("%s: %s" % (part.name, result["exception"]))
                return None

            self.ctx.stats_parts_instantiated += 1

            if result["shapes"] is None:
                return None
            if len(result["shapes"]) == 0:
                return None
            if len(result["shapes"]) == 1:
                return result["shapes"][0]

            builder = TopoDS_Builder()
            compound = TopoDS_Compound()
            builder.MakeCompound(compound)
            for shape in result["shapes"]:
                builder.Add(compound, shape)
            return compound
