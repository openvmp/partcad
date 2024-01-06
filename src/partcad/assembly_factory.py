#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-09-30
#
# Licensed under Apache License, Version 2.0.
#

import os

from . import assembly


class AssemblyFactory:
    def __init__(self, ctx, project, assembly_config, extension=""):
        self.ctx = ctx
        self.project = project
        self.name = assembly_config["name"]

        self.path = self.name + extension
        if "path" in assembly_config:
            self.path = assembly_config["path"]
        if not os.path.isdir(project.path):
            raise Exception("ERROR: The project path must be a directory")
        self.path = os.path.join(project.path, self.path)
        if not os.path.exists(self.path):
            raise Exception("ERROR: The assembly path must exist")

        # Pass the autodetected path to the 'Assembly' class
        assembly_config["path"] = self.path

    def _create(self, assembly_config):
        self.assembly = assembly.Assembly(self.name, assembly_config)

    def _save(self):
        self.project.assemblies[self.name] = self.assembly
