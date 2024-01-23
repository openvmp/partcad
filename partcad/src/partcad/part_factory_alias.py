#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-22
#
# Licensed under Apache License, Version 2.0.
#

from . import part_factory as pf


class PartFactoryAlias(pf.PartFactory):
    def __init__(self, ctx, project, part_config):
        super().__init__(ctx, project, part_config)
        # Complement the config object here if necessary
        self._create(part_config)

        self.target_part: str = part_config["target"]
        if ":" in self.target_part:
            self.target_project, self.target_part = self.target_part.split(":")
        elif "project" in part_config:
            self.target_project = part_config["project"]
        else:
            self.target_project = None

        if self.target_project is None:
            self.part.desc = "Alias to %s" % self.target_part
        else:
            self.part.desc = "Alias to %s from %s" % (
                self.target_part,
                self.target_project,
            )

    def instantiate(self, part):
        if self.target_project is None:
            target = self.project.get_part(self.target_part)
        else:
            target = self.project.ctx.get_part(self.target_part, self.target_project)

        # TODO(clairbee): resolve the absolute package path
        part.set_shape(target.get_shape())

        self.ctx.stats_parts_instantiated += 1
