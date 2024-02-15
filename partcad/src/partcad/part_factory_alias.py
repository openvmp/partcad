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


class PartFactoryAlias(pf.PartFactory):
    target_part: str
    target_project: typing.Optional[str]

    def __init__(self, ctx, project, part_config):
        with pc_logging.Action("InitAlias", project.name, part_config["name"]):
            super().__init__(ctx, project, part_config)
            # Complement the config object here if necessary
            self._create(part_config)

            self.target_part = part_config["target"]
            if "project" in part_config:
                self.target_project = part_config["project"]
            else:
                self.target_project = project.name

            pc_logging.debug(
                "Initializing an alias to %s:%s"
                % (self.target_project, self.target_part)
            )

            # Get the config of the part the alias points to
            if self.target_project == "this":
                self.part.desc = "Alias to %s" % self.target_part
            else:
                self.part.desc = "Alias to %s from %s" % (
                    self.target_part,
                    self.target_project,
                )

    def instantiate(self, part):
        with pc_logging.Action("Alias", part.project_name, part.name):
            # TODO(clairbee): resolve the absolute package path?

            target = self.ctx._get_part(self.target_part, self.target_project)
            shape = target.shape
            if not shape is None:
                return shape

            self.ctx.stats_parts_instantiated += 1

            return target.instantiate(part)
