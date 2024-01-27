#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-22
#
# Licensed under Apache License, Version 2.0.
#

import os

from . import part as p
from . import part_factory as pf


class PartFactoryFile(pf.PartFactory):
    part: p.Part

    def __init__(self, ctx, project, part_config, extension=""):
        super().__init__(ctx, project, part_config)

        if "path" in part_config:
            self.path = part_config["path"]
        else:
            self.path = self.orig_name + extension

        if not os.path.isdir(project.config_dir):
            raise Exception(
                "ERROR: The project config directory must be a directory, found: '%s'"
                % project.config_dir
            )
        self.path = os.path.join(project.config_dir, self.path)
        if not os.path.isfile(self.path):
            raise Exception("ERROR: The part path (%s) must be a file" % self.path)
