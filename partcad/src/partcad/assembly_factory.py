#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-09-30
#
# Licensed under Apache License, Version 2.0.
#

import typing

from .assembly import Assembly


# TODO(clairbee): introduce ShapeFactory
class AssemblyFactory:
    # TODO(clairbee): Make the next line work for assembly_factory_file only
    path: typing.Optional[str] = None
    assembly: Assembly

    def __init__(self, ctx, project, assembly_config, extension=""):
        self.ctx = ctx
        self.project = project
        self.assembly_config = assembly_config
        self.name = assembly_config["name"]
        self.orig_name = assembly_config["orig_name"]

    def _create(self, assembly_config):
        self.assembly = Assembly(assembly_config)
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

        self.ctx.stats_assemblies += 1
