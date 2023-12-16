#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

from . import project as p


class ImportConfiguration:
    def __init__(self, config_obj={}):
        self.config_obj = config_obj
        self.import_config_name = self.config_obj.get("name")
        self.import_config_type = self.config_obj.get("type")


class ProjectFactory(ImportConfiguration):
    def __init__(self, ctx, parent, import_config_obj, name):
        super().__init__(import_config_obj)
        self.ctx = ctx
        self.parent = parent

        if not name is None:
            self.import_config_name = name

        if parent is None:
            self.config_dir = ctx.config_dir
        else:
            self.config_dir = parent.config_dir

        # TODO(clairbee): Make project cache path a function of the project
        #                 config not just its name
        self.cache_path = (
            self.config_dir + "/.partcad/projects/" + self.import_config_name
        )

        # TODO(clairbee): Initialize the config object if necessary

    def _create(self, config):
        # TODO(clairbee): Finalize the config object if necessary
        self.project = p.Project(self.ctx, self.path)

    def _save(self):
        self.ctx.projects[self.import_config_name] = self.project
