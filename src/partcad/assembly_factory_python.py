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
from . import assembly_factory as af


class AssemblyFactoryPython(af.AssemblyFactory):
    def __init__(self, ctx, project, assembly_config):
        super().__init__(ctx, project, assembly_config, extension=".py")
        # Complement the config object here if necessary
        self._create(assembly_config)

        cadquery_script = open(self.path, "r").read()
        script = cqgi.parse(cadquery_script)
        self.assembly.set_script(script)

        self._save()
