#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-04-21
#
# Licensed under Apache License, Version 2.0.
#

from .geom import Location
from . import logging as pc_logging
from .utils import resolve_resource_path


class InterfaceInherits:
    """One of the other interface types inherited by this interface.
    May include multiple instances of each inherited interface.

    This object is contained in the 'inherits' section of an interface
    or the 'implements' section of a part/assembly.
    It points at the interface object that already exists in the package."""

    source_project_name: str
    source_sketch_name: str
    interface = None
    instances: dict[str, Location]

    def __init__(self, name, project, config: dict = {}):
        self.instances = {}
        # Resolve the interface by name
        if ":" in name:
            self.source_project_name, self.source_sketch_name = (
                resolve_resource_path(
                    project.name,
                    name,
                )
            )
            self.name = self.source_project_name + ":" + self.source_sketch_name
            self.interface = project.ctx.get_interface(self.name)
        else:
            self.source_project_name = project.name
            self.source_sketch_name = name
            self.name = self.source_project_name + ":" + self.source_sketch_name
            self.interface = project.get_interface(name)

        if self.interface is None:
            pc_logging.error(
                "Failed to find the interface to inherit: %s" % name
            )

        pc_logging.debug("Inherited config: %s: %s" % (name, str(config)))
        if config is None:
            config = {"": None}
        elif isinstance(config, str):
            config = {config: None}
        elif isinstance(config, list):
            if (
                len(config) == 3
                and isinstance(config[0], list)
                and len(config[0]) == 3
                and isinstance(config[1], list)
                and len(config[1]) == 3
                and (isinstance(config[2], int) or isinstance(config[2], float))
            ):
                # This is a single instance with a location
                config = {"": config}
            else:
                # This is a list of instances without locations
                # TODO(clairbee): is this practical at all?
                config = {instance_name: None for instance_name in config}
        elif not isinstance(config, dict):
            raise Exception(
                "Invalid 'inherits' section in the interface '%s'" % self.name
            )
        pc_logging.debug(
            "Normalized inherited config: %s: %s" % (name, str(config))
        )

        for instance_name, instance_location_config in config.items():
            if instance_location_config is None:
                location = Location()
            else:
                location = Location(instance_location_config)
            self.instances[instance_name] = location
