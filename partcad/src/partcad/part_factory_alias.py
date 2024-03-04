#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-22
#
# Licensed under Apache License, Version 2.0.
#

import typing

from . import part_factory as pf
from . import logging as pc_logging
from .utils import resolve_resource_path


class PartFactoryAlias(pf.PartFactory):
    source_part_name: str
    source_project_name: typing.Optional[str]
    source: str

    def __init__(self, ctx, source_project, target_project, part_config):
        with pc_logging.Action(
            "InitAlias", target_project.name, part_config["name"]
        ):
            super().__init__(ctx, source_project, target_project, part_config)
            # Complement the config object here if necessary
            self._create(part_config)

            if "source" in part_config:
                self.source_part_name = part_config["source"]
            else:
                self.source_assembly_name = part_config["name"]
                if not "project" in part_config:
                    raise Exception(
                        "Alias needs either the source part name or the source project name"
                    )

            if "project" in part_config:
                self.source_project_name = part_config["project"]
                if (
                    self.source_project_name == "this"
                    or self.source_project_name == ""
                ):
                    self.source_project_name = source_project.name
            else:
                if ":" in self.source_part_name:
                    self.source_project_name, self.source_part_name = (
                        resolve_resource_path(
                            source_project.name,
                            self.source_part_name,
                        )
                    )
                else:
                    self.source_project_name = source_project.name
            self.source = self.source_project_name + ":" + self.source_part_name

            if self.source_project_name == target_project.name:
                self.part.desc = "Alias to %s" % self.source_part_name
            else:
                self.part.desc = "Alias to %s from %s" % (
                    self.source_part_name,
                    self.source_project_name,
                )

            pc_logging.debug("Initializing an alias to %s" % self.source)

    def instantiate(self, part):
        with pc_logging.Action("Alias", part.project_name, part.name):

            source = self.ctx._get_part(self.source)
            shape = source.shape
            if not shape is None:
                return shape

            self.ctx.stats_parts_instantiated += 1

            return source.instantiate(part)
