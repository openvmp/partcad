#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-26
#
# Licensed under Apache License, Version 2.0.
#


import os

from .assembly_factory import AssemblyFactory
from . import logging as pc_logging


class AssemblyFactoryFile(AssemblyFactory):
    def __init__(self, ctx, project, config, extension=""):
        super().__init__(ctx, project, config)

        if "path" in config:
            self.path = config["path"]
        else:
            self.path = self.orig_name + extension

        if not os.path.isdir(project.config_dir):
            raise Exception(
                "ERROR: The project config directory must be a directory, found: '%s'"
                % project.config_dir
            )
        self.path = os.path.join(project.config_dir, self.path)
        if not os.path.exists(self.path):
            raise Exception("ERROR: The assembly path must exist")

    async def instantiate(self, assembly):
        if not self.fileFactory is None and not os.path.exists(assembly.path):
            with pc_logging.Action(
                "File", self.target_project.name, assembly.name
            ):
                await self.fileFactory.download(assembly.path)
