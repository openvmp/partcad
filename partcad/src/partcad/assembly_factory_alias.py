#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-26
#
# Licensed under Apache License, Version 2.0.
#

import typing

from . import assembly_factory as pf
from . import logging as pc_logging


class AssemblyFactoryAlias(pf.AssemblyFactory):
    target_assembly: str
    target_project: typing.Optional[str]

    def __init__(self, ctx, project, assembly_config):
        with pc_logging.Action("InitAlias", project.name, assembly_config["name"]):
            super().__init__(ctx, project, assembly_config)
            # Complement the config object here if necessary
            self._create(assembly_config)

            self.target_assembly = assembly_config["target"]
            if "project" in assembly_config:
                self.target_project = assembly_config["project"]
            else:
                self.target_project = project.name

            pc_logging.debug(
                "Initializing an alias to %s:%s"
                % (self.target_project, self.target_assembly)
            )

            # Get the config of the assembly the alias points to
            if self.target_project is None:
                self.assembly.desc = "Alias to %s" % self.target_assembly
            else:
                self.assembly.desc = "Alias to %s from %s" % (
                    self.target_assembly,
                    self.target_project,
                )

    def instantiate(self, assembly):
        with pc_logging.Action(
            "Alias", self.project.name, self.assembly_config["name"]
        ):
            self.ctx.stats_assemblies_instantiated += 1

            # TODO(clairbee): resolve the absolute package path?
            target = self.ctx._get_assembly(self.target_assembly, self.target_project)
            target.instantiate(assembly)
