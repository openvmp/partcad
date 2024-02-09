#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import cadquery as cq

from . import logging as pc_logging
from . import part_factory_file as pff


class PartFactoryStep(pff.PartFactoryFile):
    def __init__(self, ctx, project, part_config):
        with pc_logging.Action("InitSTEP", project.name, part_config["name"]):
            super().__init__(ctx, project, part_config, extension=".step")
            # Complement the config object here if necessary
            self._create(part_config)

    def instantiate(self, part):
        with pc_logging.Action("STEP", self.project.name, self.part_config["name"]):
            shape = cq.importers.importStep(self.path).val().wrapped
            part.set_shape(shape)

            self.ctx.stats_parts_instantiated += 1
