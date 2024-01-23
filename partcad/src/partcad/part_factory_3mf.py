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


class PartFactory3mf(pff.PartFactoryFile):
    def __init__(self, ctx, project, part_config):
        super().__init__(ctx, project, part_config, extension=".3mf")
        # Complement the config object here if necessary
        self._create(part_config)

    def instantiate(self, part):
        shape = b3d.Mesher().read(self.path)[0].wrapped
        part.set_shape(shape)

        self.ctx.stats_parts_instantiated += 1
