#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-26
#
# Licensed under Apache License, Version 2.0.
#

import copy
import logging
import typing

from . import part_config
from . import part_factory as pf


class PartFactoryEnrich(pf.PartFactory):
    target_part: str
    target_project: typing.Optional[str]

    def __init__(self, ctx, project, config):
        super().__init__(ctx, project, config)

        # Determine the part the 'enrich' points to
        # TODO(clairbee): refactor this using the resource locator when available
        self.target_part = config["target"]
        if "project" in config:
            self.target_project = config["project"]
        else:
            self.target_project = None

        logging.debug(
            "Initializing an enrich to %s:%s" % (self.target_project, self.target_part)
        )

        # Get the config of the part the 'enrich' points to
        if self.target_project is None:
            augmented_config = project.get_part_config(self.target_part)
        else:
            augmented_config = ctx.get_project(self.target_project).get_part_config(
                self.target_part
            )
        if augmented_config is None:
            logging.error("Failed to find the part to enrich: %s" % self.target_part)
            return

        augmented_config = copy.deepcopy(augmented_config)
        # TODO(clairbee): ideally whatever we pull from the project is already normalized
        augmented_config = part_config.PartConfiguration.normalize(
            self.target_part, augmented_config
        )

        # Drop fields we don't want to be inherited by enriched clones
        # TODO(clairbee): keep aliases if they are a function of the orignal name
        if "aliases" in augmented_config:
            del augmented_config["aliases"]

        # Fill in all non-enrich-specific properties from the enrich config into
        # the original config
        for prop_to_copy in config:
            if (
                prop_to_copy == "type"
                or prop_to_copy == "path"
                or prop_to_copy == "orig_name"
                or prop_to_copy == "target"
                or prop_to_copy == "project"
                or prop_to_copy == "with"
            ):
                continue
            augmented_config[prop_to_copy] = config[prop_to_copy]

        # Fill in the parameter values using the simplified "with" option
        if "with" in config:
            for param in config["with"]:
                augmented_config["parameters"][param]["default"] = config["with"][param]

        project.init_part_by_config(augmented_config)
