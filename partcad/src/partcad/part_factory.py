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
    name: str
    orig_name: str

    def __init__(
        self,
        ctx,
        source_project,
        target_project,
        part_config: object,
    ):
        self.ctx = ctx
        self.project = source_project
        self.target_project = target_project
        self.part_config = part_config
        self.name = part_config["name"]
        self.orig_name = part_config["orig_name"]

    def _create_part(self, part_config: object) -> p.Part:
        part = p.Part(part_config)
        part.project_name = (
            self.target_project.name
        )  # TODO(clairbee): pass it via the constructor
        # TODO(clairbee): Make the next line work for part_factory_file only
        part.instantiate = lambda part_self: self.instantiate(part_self)
        return part

    def _create(self, part_config: object):
        self.part = self._create_part(part_config)
        if self.path:
            self.part.path = self.path

        self.target_project.parts[self.name] = self.part
        self.ctx.stats_parts += 1
