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
from .utils import resolve_resource_path


class AssemblyFactoryAlias(pf.AssemblyFactory):
    source_assembly_name: str
    source_project_name: typing.Optional[str]
    source: str

    def __init__(self, ctx, project, assembly_config):
        with pc_logging.Action(
            "InitAlias", project.name, assembly_config["name"]
        ):
            super().__init__(ctx, project, assembly_config)
            # Complement the config object here if necessary
            self._create(assembly_config)

            if "source" in assembly_config:
                self.source_assembly_name = assembly_config["source"]
            else:
                self.source_assembly_name = assembly_config["name"]
                if not "project" in assembly_config:
                    raise Exception(
                        "Alias needs either the source part name or the source project name"
                    )

            if "project" in assembly_config:
                self.source_project_name = assembly_config["project"]
                if (
                    self.source_project_name == "this"
                    or self.source_project_name == ""
                ):
                    self.source_project_name = project.name
            else:
                if ":" in self.source_assembly_name:
                    self.source_project_name, self.source_assembly_name = (
                        resolve_resource_path(
                            project.name,
                            self.source_assembly_name,
                        )
                    )
                else:
                    self.source_project_name = project.name
            self.source = (
                self.source_project_name + ":" + self.source_assembly_name
            )

            if self.source_project_name == project.name:
                self.assembly.desc = "Alias to %s" % self.source_assembly_name
            else:
                self.assembly.desc = "Alias to %s from %s" % (
                    self.source_assembly_name,
                    self.source_project_name,
                )

            pc_logging.debug("Initializing an alias to %s" % self.source)

    def instantiate(self, assembly):
        with pc_logging.Action("Alias", assembly.project_name, assembly.name):

            source = self.ctx._get_assembly(self.source)
            shape = source.shape
            if not shape is None:
                assembly.shape = shape
                return

            self.ctx.stats_assemblies_instantiated += 1

            source.instantiate(assembly)
