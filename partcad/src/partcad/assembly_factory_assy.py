#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-06
#
# Licensed under Apache License, Version 2.0.
#

import build123d as b3d
from jinja2 import Environment, FileSystemLoader
import logging
import os
import yaml

from .assembly import Assembly
from . import assembly_factory_file as aff


class AssemblyFactoryAssy(aff.AssemblyFactoryFile):
    def __init__(self, ctx, project, assembly_config):
        super().__init__(ctx, project, assembly_config, extension=".assy")
        # Complement the config object here if necessary
        self._create(assembly_config)

    def instantiate(self, assembly):
        self.assy = {}
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
            self.config_text = config

            # Parse the resulting config
            try:
                self.assy = yaml.safe_load(config)
            except Exception as e:
                logging.error("ERROR: Failed to parse the assembly file %s" % self.path)
            if self.assy is None:
                self.assy = {}
        else:
            logging.error("ERROR: Assembly file not found: %s" % self.path)

        if "links" in self.assy and not self.assy["links"] is None:
            self.handle_node_list(assembly, self.assy["links"])

        self.ctx.stats_assemblies_instantiated += 1

    def handle_node_list(self, assembly, node_list):
        for link in node_list:
            self.handle_node(assembly, link)

    def handle_node(self, assembly, node):
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
        if "links" in node:
            item = Assembly(
                {"name": name}
            )  # TODO(clairbee): revisit why node["links"]) was used there
            item.instantiate = lambda x: True
            self.handle_node_list(item, node["links"])
        else:
            # This is a node for a part
            if "package" in node:
                package_name = node["package"]
            else:
                package_name = "this"
            part_name = node["part"]
            item = self.ctx.get_part(part_name, package_name)

        if not item is None:
            assembly.add(item, name, location)
        else:
            logging.error("Part not found: %s" % name)
