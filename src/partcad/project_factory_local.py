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

        if not self.import_config_path.startswith("/") and self.config_dir != "":
            self.import_config_path = self.config_dir + "/" + self.import_config_path

        self.path = self.import_config_path
        if not os.path.exists(self.import_config_path):
            raise Exception("PartCAD project not found: %s" % self.import_config_path)

        # Complement the config object here if necessary
        self._create(config)

        # Override the project path
        # TODO(clairbee): consider installing a symlink in the project cache

        # for part_config_file in glob.glob(path + "/**/part.json"):
        #     part_config = json.load(open(part_config_file, "r"))

        #     # Complement the config object here
        #     part_config["path"] = os.path.dirname(part_config_file)

        #     # Now store the part configuration in the project object
        #     part_name = part_config["name"]
        #     self.project.part_configs[part_name] = part_config

        self._save()
