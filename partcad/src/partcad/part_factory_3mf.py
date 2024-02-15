#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-01-06
#
# Licensed under Apache License, Version 2.0.
#

import build123d as b3d

from . import part_factory_file as pff
from . import logging as pc_logging


class PartFactory3mf(pff.PartFactoryFile):
    def __init__(self, ctx, project, part_config):
        with pc_logging.Action("Init3MF", project.name, part_config["name"]):
            super().__init__(ctx, project, part_config, extension=".3mf")
            # Complement the config object here if necessary
            self._create(part_config)

    def instantiate(self, part):
        with pc_logging.Action("3MF", part.project_name, part.name):
            shape = b3d.Mesher().read(self.path)[0].wrapped

            self.ctx.stats_parts_instantiated += 1

            return shape
