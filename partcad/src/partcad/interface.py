#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-04-20
#
# Licensed under Apache License, Version 2.0.
#

import asyncio

from .geom import Location
from .interface_inherit import InterfaceInherits
from .sketch import Sketch
from . import logging as pc_logging
from .utils import resolve_resource_path


class InterfacePort:
    """One of the ports provided by the interface,
    either explicitly (inside "ports:")
    or implicitly (inherited from "inherits:")."""

    name: str
    location: Location = None
    source_project_name: str
    source_sketch_name: str
    source_sketch_spec: str
    sketch: Sketch = None

    def __init__(
        self,
        name,
        project,
        config: dict = {},
        sketch: Sketch = None,
        location: Location = None,
    ):
        self.name = name

        if location is not None:
            self.location = location
        elif config.get("location", None) is not None:
            self.location = Location(config["location"])

        if sketch is not None:
            self.sketch = sketch
        elif "sketch" in config:
            if "project" in config:
                self.source_project_name = config["project"]
                if (
                    self.source_project_name == "this"
                    or self.source_project_name == ""
                ):
                    self.source_project_name = project.name
            else:
                self.source_project_name = project.name

            self.source_sketch_name = config["sketch"]
            if ":" in self.source_sketch_name:
                self.source_project_name, self.source_sketch_name = (
                    resolve_resource_path(
                        self.source_project_name,
                        self.source_sketch_name,
                    )
                )
                self.source_sketch_spec = (
                    self.source_project_name + ":" + self.source_sketch_name
                )
                self.sketch = project.ctx.get_sketch(self.source_sketch_spec)
            else:
                self.source_project_name = project.name
                self.source_sketch_spec = (
                    self.source_project_name + ":" + self.source_sketch_name
                )
                self.sketch = project.get_sketch(self.source_sketch_name)


# TODO(clairbee): introduce "Entity" as a shared parent to Shape and Interface
#                 to share "show()"
class Interface:
    """Stored as a singleton in the package and defines the interface.
    Explicitly contains all inherited ports and instances of sub-interfaces.
    """

    name: str
    full_name: str  # including project name
    desc: str
    abstract: bool

    ports: dict[str, InterfacePort]  # both own and inherited
    inherits: dict[str, InterfaceInherits]
    compatible_with: list[
        str
    ]  # list of ancestor interfaces with the same ports

    count: int

    def __init__(
        self,
        name: str,
        project,
        config: dict = {},
        config_section: str = "inherits",
    ):
        self.name = name
        self.full_name = project.name + ":" + name
        self.desc = config.get("desc", "")
        self.abstract = config.get("abstract", False)

        self.ports = {}
        self.inherits = {}
        self.compatible_with = set()

        self.count = 0

        pc_logging.debug("Initializing interface: %s" % name)

        if config.get("ports", None) is not None:
            ports_config = config["ports"]
            if isinstance(ports_config, list):
                ports_config = {port_name: {} for port_name in ports_config}
            elif isinstance(ports_config, str):
                ports_config = {ports_config: {}}
            elif not isinstance(ports_config, dict):
                raise Exception(
                    "Invalid 'ports' section in the interface '%s'" % self.name
                )

            for port_name, port_config in ports_config.items():
                self.ports[port_name] = InterfacePort(
                    port_name, project, port_config
                )

        if config.get(config_section, None) is not None:
            inherits_config = config[config_section]
            if isinstance(inherits_config, str):
                inherits_config = {inherits_config: {}}

            if len(inherits_config.keys()) == 1 and (
                isinstance(list(inherits_config.values())[0], str)
                or len(list(inherits_config.values())[0]) == 1
            ):
                compatible_with_parents = True
            else:
                compatible_with_parents = False

            for interface_name, interface_config in inherits_config.items():
                inherit = InterfaceInherits(
                    interface_name, project, interface_config
                )
                if inherit.interface is None:
                    pc_logging.error(
                        "Failed to inherit interface: %s" % interface_name
                    )
                    continue
                self.inherits[inherit.name] = inherit

                if compatible_with_parents:
                    self.compatible_with.add(inherit.name)
                    self.compatible_with = self.compatible_with.union(
                        inherit.interface.compatible_with
                    )

                for (
                    instance_name,
                    instance_location,
                ) in inherit.instances.items():
                    pc_logging.debug(
                        "Inherited ports: %s" % str(inherit.interface.ports)
                    )
                    for port_name, port in inherit.interface.ports.items():
                        if instance_name != "":
                            inherited_port_name = (
                                instance_name + "-" + port_name
                            )
                        else:
                            inherited_port_name = port_name

                        if port.location is None:
                            port_location = instance_location
                        else:
                            trsf = port.location.wrapped.Transformation()
                            pc_logging.debug(
                                "Instance location: %s" % instance_location
                            )
                            trsf.PreMultiply(
                                instance_location.wrapped.Transformation()
                            )
                            port_location = Location(trsf)
                            pc_logging.debug(
                                "Result location: %s" % port_location
                            )
                        pc_logging.debug(
                            "Inherited port from %s to %s at %s: %s"
                            % (
                                interface_name,
                                instance_name,
                                name,
                                inherited_port_name,
                            )
                        )
                        self.ports[inherited_port_name] = InterfacePort(
                            inherited_port_name,
                            project,
                            sketch=port.sketch,
                            location=port_location,
                        )

        mates = config.get("mates", None)
        if not mates is None:
            if self.abstract:
                pc_logging.error(
                    "Abstract interfaces cannot have mates: %s" % self.name
                )
                return

            if isinstance(mates, str):
                mates = {mates: {}}
            elif isinstance(mates, list):
                mates = {x: {} for x in mates}
            elif not isinstance(mates, dict):
                raise Exception(
                    "Invalid 'mates' section in the interface '%s'" % self.name
                )

            self.add_mates(project, mates)

    def add_mates(self, project, mates: dict):
        """Handles the "mates" sub-section of this interface's config,
        or the references to this interface in top level "mates" config sections
        of any project."""
        for target_interface_name, mate_target_config in mates.items():
            if not ":" in target_interface_name:
                target_interface_name = (
                    project.name + ":" + target_interface_name
                )
            target_package_name, short_target_interface_name = (
                resolve_resource_path(project.name, target_interface_name)
            )

            if target_package_name == project.name:
                target_project = project
            else:
                target_project = project.ctx.get_project(target_package_name)
            if target_project is None:
                pc_logging.error(
                    "Failed to find the target package: %s"
                    % target_package_name
                )
                continue
            target_interface = target_project.get_interface(
                short_target_interface_name
            )
            if target_interface is None:
                pc_logging.error(
                    "Failed to find the target interface: %s"
                    % target_interface_name
                )
                continue
            if target_interface.abstract:
                pc_logging.error(
                    "Cannot mate with an abstract interface: %s"
                    % target_interface_name
                )
                continue
            project.ctx.add_mate(self, target_interface, mate_target_config)

    def info(self):
        return {
            "name": self.name,
            "desc": self.desc,
            "ports": self.ports,
            "inherits": self.inherits,
        }

    async def get_components(self):
        components = []
        for port in self.ports.values():
            components.append(port.location)
            if port.sketch is not None:
                sketch_components = list(await port.sketch.get_components())

                def move_component(component, move_components):
                    nonlocal port
                    if isinstance(component, list):
                        component = move_components(component)
                    else:
                        component = component.Located(port.location.wrapped)
                    return component

                def move_components(components):
                    components = list(
                        map(
                            lambda x: move_component(x, move_components),
                            components,
                        )
                    )
                    return components

                sketch_components = move_components(sketch_components)
                components.append(sketch_components)
        return components

    async def show_async(self):
        components = []
        try:
            components = await self.get_components()
        except Exception as e:
            pc_logging.error(e)

        if len(components) != 0:
            import importlib

            ocp_vscode = importlib.import_module("ocp_vscode")
            if ocp_vscode is None:
                pc_logging.warning(
                    'Failed to load "ocp_vscode". Giving up on connection to VS Code.'
                )
            else:
                try:
                    pc_logging.info('Visualizing in "OCP CAD Viewer"...')
                    ocp_vscode.show(
                        *components,
                        progress=None,
                        # TODO(clairbee): make showing (and the connection
                        # to ocp_vscode) a part of the context, and memorize
                        # which part was displayed last. Keep the camera
                        # if the part has not changed.
                        # reset_camera=ocp_vscode.Camera.KEEP,
                    )
                except Exception as e:
                    pc_logging.warning(e)
                    pc_logging.warning(
                        'No VS Code or "OCP CAD Viewer" extension detected.'
                    )

    def show(self):
        asyncio.run(self.show_async())
