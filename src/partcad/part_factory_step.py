#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import cadquery as cq
from . import part_factory as pf
from . import part as p


class PartFactoryStep(pf.PartFactory):
    def __init__(self, ctx, project, part_config):
        super().__init__(ctx, project, part_config, extension=".step")
        # Complement the config object here if necessary
        self._create(part_config)

        shape = cq.importers.importStep(self.path).val().wrapped
        self.part.set_shape(shape)

        self._save()
