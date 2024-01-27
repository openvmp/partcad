#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import os

from . import project as p


class ImportConfiguration:
    def __init__(self, config_obj={}):
        self.config_obj = config_obj
        self.name = self.config_obj.get("name")
        self.import_config_type = self.config_obj.get("type")


class ProjectFactory(ImportConfiguration):
    def __init__(self, ctx, parent, import_config_obj):
        super().__init__(import_config_obj)
        self.ctx = ctx
        self.parent = parent

        if parent is None:
            self.config_path = ctx.config_path
            self.config_dir = ctx.config_dir
        else:
            self.config_path = parent.config_path
            self.config_dir = parent.config_dir

        # TODO(clairbee): Initialize the config object if necessary

    def _create(self, config):
        # TODO(clairbee): Finalize the config object if necessary
        self.project = p.Project(self.ctx, self.name, self.path)
        # Make the project config inherit some properties of the import config
        self.project.config_obj["type"] = self.import_config_type

    def _save(self):
        self.ctx.projects[self.name] = self.project
