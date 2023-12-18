#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

from cadquery import cqgi
from . import part_factory as pf


class PartFactoryCadquery(pf.PartFactory):
    def __init__(self, ctx, project, part_config):
        super().__init__(ctx, project, part_config, extension=".py")
        # Complement the config object here if necessary
        self._create(part_config)

        cadquery_script = open(self.path, "r").read()
        if "import partcad as pc" in cadquery_script:
            cadquery_script += "\npc.finalize_real()\n"
        print(cadquery_script)
        script = cqgi.parse(cadquery_script)
        result = script.build(build_parameters={})
        if result.success:
            self.part.shape = result.first_result.shape
        else:
            print(result.exception)

        self._save()
