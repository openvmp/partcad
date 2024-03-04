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
from . import logging as pc_logging


class PartFactoryFile(pf.PartFactory):
    part: p.Part

    def __init__(
        self, ctx, source_project, target_project, part_config, extension=""
    ):
        super().__init__(ctx, source_project, target_project, part_config)

        if "path" in part_config:
            self.path = part_config["path"]
        else:
            self.path = self.orig_name + extension

        if not os.path.isdir(source_project.config_dir):
            raise Exception(
                "ERROR: The project config directory must be a directory, found: '%s'"
                % source_project.config_dir
            )
        self.path = os.path.join(source_project.config_dir, self.path)
        if not os.path.isfile(self.path):
            raise Exception(
                "ERROR: The part path (%s) must be a file" % self.path
            )
