#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-06
#
# Licensed under Apache License, Version 2.0.
#

import asyncio
from jinja2 import Environment, FileSystemLoader
import os
import yaml

from OCP.gp import gp_Trsf
import build123d as b3d

from .assembly import Assembly, AssemblyChild
from .assembly_factory_file import AssemblyFactoryFile
from . import logging as pc_logging
from .utils import normalize_resource_path


class AssemblyFactoryAssy(AssemblyFactoryFile):
    def __init__(self, ctx, project, config):
        with pc_logging.Action("InitASSY", project.name, config["name"]):
            super().__init__(ctx, project, config, extension=".assy")
            # Complement the config object here if necessary
            self._create(config)

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
        await super().instantiate(assembly)

        with pc_logging.Action("ASSY", assembly.project_name, assembly.name):
            assy = {}
            if os.path.exists(self.path):
                params = {}
                if "parameters" in self.config:
                    for param_name, param in self.config["parameters"].items():
                        params["param_" + param_name] = param["default"]
                params["name"] = self.config["name"]

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

        async def wait_for_tasks():
            nonlocal tasks
            while len(tasks) > 0:
                task = tasks.pop(0)
                f = await asyncio.tasks.wait([task])
                result = f[0].pop().result()
                if not result is None:
                    assembly.children.append(
                        AssemblyChild(result[0], result[1], result[2])
                    )
                    # Keep part reference counter for bill-of-materials purposes
                    result[0].ref_inc()

        for link in node_list:
            if "connect" in link:
                # wait for all previous nodes to get added first
                await wait_for_tasks()
            tasks.append(self.handle_node(assembly, link))
        await wait_for_tasks()

    async def handle_node(self, assembly, node):
        # "name" is an optional parameter for both parts and assemblies
        if "name" in node:
            name = node["name"]
        else:
            name = None

        connect = None
        connect_with_iface = None
        connect_with_port = None
        connect_with_instance = None
        connect_to_name = None
        connect_to_iface = None
        connect_to_port = None
        connect_to_instance = None
        # "location" is an optional parameter for both parts and assemblies
        if "location" in node:
            l = node["location"]
            location = b3d.Location(
                (l[0][0], l[0][1], l[0][2]), (l[1][0], l[1][1], l[1][2]), l[2]
            )
        elif "connect" in node:
            connect = node["connect"]
            connect_with_iface = connect.get("with", None)
            if connect_with_iface is not None and ":" not in connect_with_iface:
                connect_with_iface = (
                    self.project.name + ":" + connect_with_iface
                )
            connect_with_port = connect.get("withPort", None)
            connect_with_instance = connect.get("withInstance", None)

            connect_to_name = connect.get("name", None)

            connect_to_iface = connect.get("to", None)
            if connect_to_iface is not None and ":" not in connect_to_iface:
                connect_to_iface = self.project.name + ":" + connect_to_iface
            connect_to_port = connect.get("toPort", None)
            connect_to_instance = connect.get("toInstance", None)
            location = None
        elif "connectPorts" in node:
            connect = node["connectPorts"]
            connect_with_port = connect.get("with", None)
            connect_to_name = connect.get("name", None)
            connect_to_port = connect.get("to", None)
            location = None
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
                if name is None:
                    name = assy_name
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
                if name is None:
                    name = part_name
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

            if connect is not None:
                pc_logging.info("Attempting to connect %s" % name)
                source_port = None
                source_iface = None
                source_iface_instance = None
                target_part = None
                target_part_location = None
                target_port = None
                target_iface = None
                target_iface_instance = None
                # trsf = None # TODO(clairbee): implement offsets

                for child in assembly.children:
                    if hasattr(child, "name") and child.name == connect_to_name:
                        # pc_logging.info(
                        #     "Found target part: %s" % connect_to_name
                        # )

                        target_part = child.item
                        break

                if target_part is None:
                    pc_logging.error(
                        "Target part not found: %s" % connect_to_name
                    )
                else:
                    if hasattr(child, "location"):
                        target_part_location = child.location
                    else:
                        target_part_location = b3d.Location(
                            (0, 0, 0), (0, 0, 1), 0
                        )

                    source_candidate_interfaces, target_candidate_interfaces = (
                        self.project.ctx.find_mating_interfaces(
                            item, target_part
                        )
                    )

                    if connect_with_port is None and connect_with_iface is None:
                        if len(source_candidate_interfaces) == 1:
                            connect_with_iface = (
                                source_candidate_interfaces.pop()
                            )
                        elif len(source_candidate_interfaces) > 1:
                            pc_logging.debug(
                                "Multiple source interfaces are candidates for connection: %s"
                                % source_candidate_interfaces
                            )
                        else:
                            pc_logging.debug(
                                "No source interfaces are candidates for connection"
                            )

                    if connect_to_port is None and connect_to_iface is None:
                        if len(target_candidate_interfaces) == 1:
                            connect_to_iface = target_candidate_interfaces.pop()
                        elif len(target_candidate_interfaces) > 1:
                            pc_logging.debug(
                                "Multiple target interfaces are candidates for connection: %s"
                                % target_candidate_interfaces
                            )
                        else:
                            pc_logging.debug(
                                "No target interfaces are candidates for connection"
                            )

                    if not connect_with_iface is None:
                        source_iface = item.with_ports.interfaces[
                            connect_with_iface
                        ]

                        if not connect_with_instance is None:
                            source_iface_instance = source_iface[
                                connect_with_instance
                            ]
                        elif len(list(source_iface.values())) == 1:
                            source_iface_instance = list(source_iface.values())[
                                0
                            ]

                        if (
                            source_iface_instance is not None
                            and len(list(source_iface_instance.values())) == 1
                            and connect_with_port is None
                        ):
                            connect_with_port = list(
                                source_iface_instance.values()
                            )[0]
                        # pc_logging.info("Found source interface: %s" % source_iface.name)

                    if not connect_with_port is None:
                        source_port = item.with_ports.ports[connect_with_port]
                        pc_logging.info(
                            "Found source port: %s" % source_port.name
                        )
                    elif len(list(item.with_ports.ports.keys())) == 1:
                        source_port = list(item.with_ports.ports.values())[0]
                    else:
                        # Source port is not configured.
                        # It needs to be guessed later, based on the peer port.
                        pass

                    if not connect_to_iface is None:
                        target_iface = target_part.with_ports.interfaces[
                            connect_to_iface
                        ]

                        if not connect_to_instance is None:
                            target_iface_instance = target_iface[
                                connect_to_instance
                            ]
                        elif len(list(target_iface.values())) == 1:
                            target_iface_instance = list(target_iface.values())[
                                0
                            ]

                        if (
                            target_iface_instance is not None
                            and len(list(target_iface_instance.values())) == 1
                            and connect_to_port is None
                        ):
                            connect_to_port = list(
                                target_iface_instance.values()
                            )[0]
                        # pc_logging.info("Found target interface: %s" % target_iface.name)

                    if (
                        source_iface_instance is not None
                        and target_iface_instance is not None
                        and source_port is None
                        and target_port is None
                    ):
                        # Both interfaces are known but they have more than one port each.
                        # Let's find a matching pair of ports.
                        source_ports = sorted(
                            list(source_iface_instance.keys())
                        )
                        target_ports = sorted(
                            list(target_iface_instance.keys())
                        )
                        if source_ports == target_ports:
                            # The interfaces have the same number of ports and the same names.
                            # We can connect them using any pair of matching ports.
                            connect_with_port = source_iface_instance[
                                source_ports[0]
                            ]
                            connect_to_port = target_iface_instance[
                                target_ports[0]
                            ]
                            source_port = item.with_ports.ports[
                                connect_with_port
                            ]
                            target_port = target_part.with_ports.ports[
                                connect_to_port
                            ]
                        elif len(source_ports) == len(target_ports):
                            # TODO(clairbee): determine the port mapping from mating
                            pc_logging.warn(
                                "Connect %s to %s: port mating is not detected deterministically, guessing alphabetically..."
                                % (name, connect_to_name)
                            )
                            connect_with_port = source_iface_instance[
                                source_ports[0]
                            ]
                            connect_to_port = target_iface_instance[
                                target_ports[0]
                            ]
                            source_port = item.with_ports.ports[
                                connect_with_port
                            ]
                            target_port = target_part.with_ports.ports[
                                connect_to_port
                            ]
                        else:
                            pc_logging.error(
                                "Port count mismatch: %s: %d vs %s: %d"
                                % (
                                    source_iface.name,
                                    len(source_ports),
                                    target_iface.name,
                                    len(target_ports),
                                )
                            )

                    if target_port is None and not connect_to_port is None:
                        target_port = target_part.with_ports.ports[
                            connect_to_port
                        ]
                        pc_logging.info(
                            "Found target port: %s" % target_port.name
                        )
                    elif len(list(item.with_ports.ports.keys())) == 1:
                        target_port = list(item.with_ports.ports.values())[0]
                    else:
                        # Target port is not configured.
                        # It needs to be guessed later, based on the peer port.
                        pass

                    if (source_port is None and target_port is not None) or (
                        source_port is not None and target_port is None
                    ):
                        pc_logging.error(
                            "Peer port auto-detection is not yet implemented: %s"
                            % name
                        )

                    if source_port is not None and target_port is not None:
                        pc_logging.info(
                            "Connected %s of %s to %s of %s"
                            % (
                                connect_with_port,
                                name,
                                connect_to_port,
                                connect_to_name,
                            )
                        )

                        trsf = target_part_location.wrapped.Transformation()
                        trsf.Multiply(
                            target_port.location.wrapped.Transformation()
                        )
                        trsf.Multiply(
                            source_port.location.wrapped.Transformation().Inverted()
                        )
                        location = b3d.Location(trsf)
                    elif source_port is None and target_port is not None:
                        pc_logging.info(
                            "Connected %s to %s of %s"
                            % (
                                name,
                                connect_to_port,
                                connect_to_name,
                            )
                        )

                        trsf = target_part_location.wrapped.Transformation()
                        trsf.Multiply(
                            target_port.location.wrapped.Transformation()
                        )
                        location = b3d.Location(trsf)
                    elif source_port is not None and target_port is None:
                        pc_logging.info(
                            "Connected %s of %s to %s"
                            % (connect_with_port, name, connect_to_name)
                        )
                        trsf = target_part_location.wrapped.Transformation()
                        trsf.Multiply(
                            source_port.location.wrapped.Transformation().Inverted()
                        )
                        location = b3d.Location(trsf)
                    elif source_port is None and target_port is None:
                        pc_logging.info(
                            "Connected %s to %s" % (name, connect_to_name)
                        )
                        location = target_part_location
                    else:
                        pc_logging.error("Not enough data to connect %s" % name)
                        location = b3d.Location((0, 0, 0), (0, 0, 1), 0)

        if not item is None:
            return [item, name, location]
        else:
            return None
