#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-03-23
#
# Licensed under Apache License, Version 2.0.
#

from .part_factory_build123d import PartFactoryBuild123d
from .part_factory_feature_ai import PartFactoryFeatureAi
from . import logging as pc_logging


class PartFactoryAiBuild123d(PartFactoryBuild123d, PartFactoryFeatureAi):
    def __init__(self, ctx, source_project, target_project, part_config):
        # Override the path determined by the parent class to enable "enrich"
        part_config["path"] = part_config["name"] + ".py"

        mode = "builder"
        if "mode" in part_config and part_config["mode"] == "algebra":
            mode = "algebra"

        with pc_logging.Action(
            "InitAiB3d", target_project.name, part_config["name"]
        ):
            PartFactoryFeatureAi.__init__(
                self,
                part_config,
                "build123d",
                "build123d script (in %s)" % mode,
                """Import all the required modules
(including 'math' and 'build123d' itself).
Do not export anything.
Use show_object() to display the part.
""",
            )
            PartFactoryBuild123d.__init__(
                self,
                ctx,
                source_project,
                target_project,
                part_config,
                can_create=True,
            )

            self.on_init_ai()
