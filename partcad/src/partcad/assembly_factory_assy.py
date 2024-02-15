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


class AssemblyFactoryAssy(aff.AssemblyFactoryFile):
    def __init__(self, ctx, project, assembly_config):
        with pc_logging.Action("InitASSY", project.name, assembly_config["name"]):
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
        with pc_logging.Action("ASSY", self.project.name, assembly.config["name"]):
            assy = {}
            if os.path.exists(self.path):
                # Read the body of the configuration file
                fp = open(self.path, "r")
                config = fp.read()
                fp.close()

                # Resolve Jinja templates
                template = Environment(
                    loader=FileSystemLoader(os.path.dirname(self.path) + os.path.sep)
                ).from_string(config)
                config = template.render(
                    name=self.assembly_config["name"],
                )

                # Parse the resulting config
                try:
                    assy = yaml.safe_load(config)
                except Exception as e:
                    pc_logging.error(
                        "ERROR: Failed to parse the assembly file %s" % self.path
                    )
                if assy is None:
                    assy = {}
            else:
                pc_logging.error("ERROR: Assembly file not found: %s" % self.path)

            result = await self.handle_node(assembly, assy)
            if not result is None:
                assembly.children.append(AssemblyChild(result[0], result[1], result[2]))
                # Keep part reference counter for bill-of-materials purposes
                await result[0].ref_inc_async()
            else:
                raise Exception("Assembly is empty")

            self.ctx.stats_assemblies_instantiated += 1

    async def handle_node_list(self, assembly, node_list):
        tasks = []
        for link in node_list:
            tasks.append(self.handle_node(assembly, link))

        # TODO(clairbee): revisit whether non-determinism is acceptable here
        for f in asyncio.as_completed(tasks):
            result = await f
            if not result is None:
                assembly.children.append(AssemblyChild(result[0], result[1], result[2]))
                # Keep part reference counter for bill-of-materials purposes
                await result[0].ref_inc_async()

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
            # This is a node for a part
            if "package" in node:
                package_name = node["package"]
            else:
                package_name = "this"
            if package_name == "this":
                package_name = self.project.name

            params = {}
            if "params" in node:
                for paramName in node["params"]:
                    params[paramName] = node["params"][paramName]

            if "assembly" in node:
                assy_name = node["assembly"]
                item = self.ctx._get_assembly(assy_name, package_name, params)
                if item is None:
                    raise Exception("Part not found")
            else:
                part_name = node["part"]
                item = self.ctx._get_part(part_name, package_name, params)
                if item is None:
                    raise Exception("Assembly not found")

        if not item is None:
            return [item, name, location]
        else:
            pc_logging.error("Part not found: %s" % name)
            return None
