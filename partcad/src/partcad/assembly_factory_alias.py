#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-26
#
# Licensed under Apache License, Version 2.0.
#

import logging
import typing

from . import assembly_factory as pf


class AssemblyFactoryAlias(pf.AssemblyFactory):
    target_assembly: str
    target_project: typing.Optional[str]

    def __init__(self, ctx, project, config):
        super().__init__(ctx, project, config)
        # Complement the config object here if necessary
        self._create(config)

        self.target_assembly = config["target"]
        if "project" in config:
            self.target_project = config["project"]
        else:
            self.target_project = None

        logging.debug(
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
        # TODO(clairbee): resolve the absolute package path?
        if self.target_project is None:
            target = self.project.get_assembly(self.target_assembly)
        else:
            target = self.project.ctx.get_assembly(
                self.target_assembly, self.target_project
            )

        assembly.set_shape(target.get_shape())

        self.ctx.stats_assemblies_instantiated += 1
