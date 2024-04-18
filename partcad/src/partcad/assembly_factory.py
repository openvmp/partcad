#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-09-30
#
# Licensed under Apache License, Version 2.0.
#

import os
import typing

from .assembly import Assembly
from .shape_factory import ShapeFactory


class AssemblyFactory(ShapeFactory):
    # TODO(clairbee): Make the next line work for assembly_factory_file only
    path: typing.Optional[str] = None
    assembly: Assembly

    def __init__(self, ctx, project, config, extension=""):
        super().__init__(ctx, project, config)
        self.name = config["name"]
        self.orig_name = config["orig_name"]

    def _create(self, config):
        self.assembly = Assembly(config)
        self.assembly.project_name = (
            self.project.name
        )  # TODO(clairbee): pass it via the constructor
        # TODO(clairbee): Make the next line work for assembly_factory_file only
        if self.path:
            self.assembly.path = self.path
        self.project.assemblies[self.name] = self.assembly

        self.assembly.instantiate = lambda assembly_self: self.instantiate(
            assembly_self
        )
        self.assembly.info = lambda: self.info(self.assembly)

        self.ctx.stats_assemblies += 1
