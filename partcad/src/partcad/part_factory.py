#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import typing

from . import part as p


class PartFactory:
    # TODO(clairbee): Make the next line work for part_factory_file only
    path: typing.Optional[str] = None
    part: p.Part

    def __init__(self, ctx, project, part_config: object, extension: str = ""):
        self.ctx = ctx
        self.project = project
        self.part_config = part_config
        self.name = part_config["name"]
        self.orig_name = part_config["orig_name"]

    def _create(self, part_config: object):
        self.part = p.Part(part_config)
        # TODO(clairbee): Make the next line work for part_factory_file only
        if self.path:
            self.part.path = self.path
        self.part.instantiate = lambda part_self: self.instantiate(part_self)

        self.project.parts[self.name] = self.part

        self.ctx.stats_parts += 1
