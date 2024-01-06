#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-06
#
# Licensed under Apache License, Version 2.0.
#

import build123d as b3d
import copy
import logging
import os
import yaml

from .assembly import Assembly
from . import assembly_factory as af


class AssemblyFactoryAssy(af.AssemblyFactory):
    def __init__(self, ctx, project, assembly_config):
        super().__init__(ctx, project, assembly_config, extension=".assy")
        # Complement the config object here if necessary
        self._create(assembly_config)

        self.assy = {}
        if os.path.exists(self.path):
            try:
                self.assy = yaml.safe_load(open(self.path))
            except Exception as e:
                logging.error("ERROR: Failed to parse the assembly file %s" % self.path)
            if self.assy is None:
                self.assy = {}
        else:
            logging.error("ERROR: Assembly file not found: %s" % self.path)

        if "links" in self.assy and not self.assy["links"] is None:
            self.handle_node_list(self.assembly, self.assy["links"])

        self._save()

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
            item = Assembly(name, node["links"])
            self.handle_node_list(item, node["links"])
        else:
            # This is a node for a part
            if "package" in node:
                package_name = node["package"]
            else:
                package_name = "this"
            part_name = node["part"]
            item = self.ctx.get_part(part_name, package_name)

        assembly.add(item, name, location)
