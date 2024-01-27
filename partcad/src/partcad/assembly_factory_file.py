#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-26
#
# Licensed under Apache License, Version 2.0.
#


import os

from . import assembly as p
from . import assembly_factory as pf


class AssemblyFactoryFile(pf.AssemblyFactory):
    assembly: p.Assembly

    def __init__(self, ctx, project, assembly_config, extension=""):
        super().__init__(ctx, project, assembly_config)

        if "path" in assembly_config:
            self.path = assembly_config["path"]
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
