#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import glob
import json
import os
from . import project_factory as pf


class LocalImportConfiguration:
    def __init__(self):
        self.import_config_path = self.config_obj.get("path")


class ProjectFactoryLocal(pf.ProjectFactory, LocalImportConfiguration):
    def __init__(self, ctx, parent, config, name=None):
        pf.ProjectFactory.__init__(self, ctx, parent, config, name)
        LocalImportConfiguration.__init__(self)

        if not os.path.isabs(self.import_config_path) and self.config_dir != "":
            self.import_config_path = os.path.join(
                self.config_dir, self.import_config_path
            )

        self.path = self.import_config_path
        if not os.path.exists(self.import_config_path):
            raise Exception("PartCAD project not found: %s" % self.import_config_path)

        # Complement the config object here if necessary
        self._create(config)

        # TODO(clairbee): consider installing a symlink in the project cache

        self._save()
