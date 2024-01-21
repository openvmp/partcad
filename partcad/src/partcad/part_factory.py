#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import os

from . import part as p


class PartFactory:
    part: p.Part

    def __init__(self, ctx, project, part_config, extension=""):
        self.ctx = ctx
        self.project = project
        self.part_config = part_config
        self.name = part_config["name"]

        self.path = self.name + extension
        if "path" in part_config:
            self.path = part_config["path"]
        if not os.path.isdir(project.config_dir):
            raise Exception(
                "ERROR: The project config directory must be a directory, found: '%s'"
                % project.config_dir
            )
        self.path = os.path.join(project.config_dir, self.path)
        if not os.path.isfile(self.path):
            raise Exception("ERROR: The part path (%s) must be a file" % self.path)

        # Pass the autodetected path to the 'Part' class
        part_config["path"] = self.path

    def _create(self, part_config):
        self.part = p.Part(self.name, self.path, part_config)

        self.project.parts[self.name] = self.part
        if "aliases" in self.part_config and not self.part_config["aliases"] is None:
            for alias in self.part_config["aliases"]:
                # TODO(clairbee): test if this a copy or a reference
                self.project.parts[alias] = self.part

        self.part.instantiate = lambda part_self: self.instantiate(part_self)

        self.ctx.stats_parts += 1
