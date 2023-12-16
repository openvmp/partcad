#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

from . import project_factory as pf


class GitImportConfiguration:
    def __init__(self):
        self.import_config_url = self.config_obj.get("url")


class ProjectFactoryGit(pf.ProjectFactory, GitImportConfiguration):
    def __init__(self, ctx, parent, config, name=None):
        pf.ProjectFactory.__init__(self, ctx, parent, config, name)
        GitImportConfiguration.__init__(self)

        # TODO(clairbee): Clone self.import_config_url to self.cache_path

        # Complement the config object here if necessary
        self.path = self.cache_path
        self._create(config)

        # TODO(clairbee): actually fill in the self.project object here

        self._save()
