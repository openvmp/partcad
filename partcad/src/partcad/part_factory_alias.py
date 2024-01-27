#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-22
#
# Licensed under Apache License, Version 2.0.
#

import logging
import typing

from . import part_factory as pf


class PartFactoryAlias(pf.PartFactory):
    target_part: str
    target_project: typing.Optional[str]

    def __init__(self, ctx, project, config):
        super().__init__(ctx, project, config)
        # Complement the config object here if necessary
        self._create(config)

        self.target_part = config["target"]
        if "project" in config:
            self.target_project = config["project"]
        else:
            self.target_project = None

        logging.debug(
            "Initializing an alias to %s:%s" % (self.target_project, self.target_part)
        )

        # Get the config of the part the alias points to
        if self.target_project is None:
            self.part.desc = "Alias to %s" % self.target_part
        else:
            self.part.desc = "Alias to %s from %s" % (
                self.target_part,
                self.target_project,
            )

    def instantiate(self, part):
        # TODO(clairbee): resolve the absolute package path?
        if self.target_project is None:
            target = self.project.get_part(self.target_part)
        else:
            target = self.project.ctx.get_part(self.target_part, self.target_project)

        part.set_shape(target.get_shape())

        self.ctx.stats_parts_instantiated += 1
