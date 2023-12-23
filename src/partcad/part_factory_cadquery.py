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


class PartFactoryCadquery(pf.PartFactory):
    def __init__(self, ctx, project, part_config):
        super().__init__(ctx, project, part_config, extension=".py")
        # Complement the config object here if necessary
        self._create(part_config)

        cadquery_script = open(self.path, "r").read()
        if "import partcad as pc" in cadquery_script:
            cadquery_script += "\npc.finalize_real()\n"
        # print(cadquery_script)
        script = cq.cqgi.parse(cadquery_script)
        result = script.build(build_parameters={})
        if result.success:
            shape = result.first_result.shape
            if not hasattr(shape, "wrapped"):
                cq_solid = cq.Solid.makeBox(1, 1, 1)
                cq_solid.wrapped = shape
                shape = cq_solid
            self.part.shape = shape
        else:
            print(result.exception)

        self._save()
