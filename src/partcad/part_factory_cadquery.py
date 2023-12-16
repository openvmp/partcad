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
        script = cqgi.parse(cadquery_script)
        result = script.build()
        if not result.success:
            print("Failed to load a cadquery part")
            print(result.exception)
            raise Exception(result.exception)
        first_result = result.first_result
        part = first_result.shape
        self.part.set_shape(part)

        self._save()
