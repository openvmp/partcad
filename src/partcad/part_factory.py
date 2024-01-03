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
    def __init__(self, ctx, project, part_config, extension=""):
        self.ctx = ctx
        self.project = project
        self.name = part_config["name"]

        self.path = self.name + extension
        if "path" in part_config:
            self.path = part_config["path"]
        if not os.path.isdir(project.path):
            raise Exception("ERROR: The project path must be a directory")
        self.path = os.path.join(project.path, self.path)
        if not os.path.exists(self.path):
            raise Exception("ERROR: The part path must exist")

        # Pass the autodetected path to the 'Part' class
        part_config["path"] = self.path

    def _create(self, part_config):
        self.part = p.Part(self.name, part_config)

    def _save(self):
        self.project.parts[self.name] = self.part
