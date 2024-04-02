#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-06
#
# Licensed under Apache License, Version 2.0.
#

import asyncio
import build123d as b3d
from jinja2 import Environment, FileSystemLoader
import os
import yaml

from .assembly import Assembly, AssemblyChild
from . import assembly_factory_file as aff
from . import logging as pc_logging
from .utils import normalize_resource_path


class AssemblyFactoryAssy(aff.AssemblyFactoryFile):
    def __init__(self, ctx, project, assembly_config):
        with pc_logging.Action(
            "InitASSY", project.name, assembly_config["name"]
        ):
            super().__init__(ctx, project, assembly_config, extension=".assy")
            # Complement the config object here if necessary
            self._create(assembly_config)

    def instantiate(self, assembly):
        # # This method is best executed on a thread but the current Python version
        # # might not be good enough to do that.
        # try:
        #     # Try running on the current event loop if any.
        #     loop = asyncio.get_running_loop()
        #     # task = loop.create_task(self.instantiate_async(assembly))
        #     # task.
        #     f = asyncio.run_coroutine_threadsafe(self.instantiate_async(assembly), loop)
        #     raise Exception("IT WORKS")
        # except RuntimeError as e:
        #     print(e)
        #     # Running on a dedicated thread and there is no event loop here yet.
        asyncio.run(self.instantiate_async(assembly))

    async def instantiate_async(self, assembly):
        with pc_logging.Action("ASSY", assembly.project_name, assembly.name):
            assy = {}
            if os.path.exists(self.path):
                params = {}
                if "parameters" in self.assembly_config:
                    for param_name, param in self.assembly_config[
                        "parameters"
                    ].items():
                        params["param_" + param_name] = param["default"]
                params["name"] = self.assembly_config["name"]

                # Read the body of the configuration file
                fp = open(self.path, "r")
                config = fp.read()
                fp.close()

                # Resolve Jinja templates
                template = Environment(
                    loader=FileSystemLoader(
                        os.path.dirname(self.path) + os.path.sep
                    )
                ).from_string(config)
                config = template.render(params)

                # Parse the resulting config
                try:
                    assy = yaml.safe_load(config)
                except Exception as e:
                    pc_logging.error(
                        "ERROR: Failed to parse the assembly file %s"
                        % self.path
                    )
                if assy is None:
                    assy = {}
            else:
                pc_logging.error(
                    "ERROR: Assembly file not found: %s" % self.path
                )

            result = await self.handle_node(assembly, assy)
            if not result is None:
                assembly.children.append(
                    AssemblyChild(result[0], result[1], result[2])
                )
                # Keep part reference counter for bill-of-materials purposes
                result[0].ref_inc()
            else:
                pc_logging.warning("Assembly is empty")

            self.ctx.stats_assemblies_instantiated += 1

    async def handle_node_list(self, assembly, node_list):
        tasks = []
        for link in node_list:
            tasks.append(self.handle_node(assembly, link))

        # TODO(clairbee): revisit whether non-determinism is acceptable here
        for f in asyncio.as_completed(tasks):
            result = await f
            if not result is None:
                assembly.children.append(
                    AssemblyChild(result[0], result[1], result[2])
                )
                # Keep part reference counter for bill-of-materials purposes
                result[0].ref_inc()

    async def handle_node(self, assembly, node):
        # "name" is an optional parameter for both parts and assemblies
        if "name" in node:
            name = node["name"]
        else:
            name = None

        # "location" is an optional parameter for both parts and assemblies
        if "location" in node:
            l = node["location"]
            location = b3d.Location(
                (l[0][0], l[0][1], l[0][2]), (l[1][0], l[1][1], l[1][2]), l[2]
            )
        else:
            location = b3d.Location((0, 0, 0), (0, 0, 1), 0)

        # Check if this node is for an assembly
        if "links" in node and not node["links"] is None:
            item = Assembly(
                {"name": name}
            )  # TODO(clairbee): revisit why node["links"]) was used there
            item.instantiate = lambda x: True
            await self.handle_node_list(item, node["links"])
        else:
            # This is a node for a part or an assembly
            params = {}
            if "params" in node:
                for paramName in node["params"]:
                    params[paramName] = node["params"][paramName]

            if "assembly" in node:
                assy_name = node["assembly"]
                if "package" in node:
                    assy_name = node["package"] + ":" + assy_name
                elif not ":" in assy_name:
                    assy_name = ":" + assy_name
                assy_name = normalize_resource_path(
                    self.project.name, assy_name
                )
                item = self.ctx._get_assembly(assy_name, params)
                if item is None:
                    pc_logging.error("Assembly not found: %s" % name)
                    raise Exception("Assembly not found")
            elif "part" in node:
                part_name = node["part"]
                if "package" in node:
                    part_name = node["package"] + ":" + part_name
                elif not ":" in part_name:
                    part_name = ":" + part_name
                part_name = normalize_resource_path(
                    self.project.name, part_name
                )
                item = self.ctx._get_part(part_name, params)
                if item is None:
                    pc_logging.error(
                        "Part not found: %s in %s" % (name, self.name)
                    )
                    raise Exception(
                        "Part not found: %s in %s" % (name, self.name)
                    )
            else:
                item = None

        if not item is None:
            return [item, name, location]
        else:
            return None
