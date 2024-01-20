#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-01-06
#
# Licensed under Apache License, Version 2.0.
#

import build123d as b3d
from . import part_factory as pf
from . import part as p


class PartFactoryStl(pf.PartFactory):
    def __init__(self, ctx, project, part_config):
        super().__init__(ctx, project, part_config, extension=".stl")
        # Complement the config object here if necessary
        self._create(part_config)

    def instantiate(self, part):
        shape = b3d.Mesher().read(part.path)[0].wrapped
        part.set_shape(shape)

        self.ctx.stats_parts_instantiated += 1
