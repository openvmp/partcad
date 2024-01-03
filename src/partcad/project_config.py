#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import json
import logging
import os
import pkg_resources
from packaging.specifiers import SpecifierSet
import yaml

DEFAULT_CONFIG_FILENAME = "partcad.yaml"


class Configuration:
    def __init__(self, config_path=DEFAULT_CONFIG_FILENAME):
        self.config_obj = {}
        self.config_dir = config_path
        self.config_path = config_path

        if os.path.isdir(config_path):
            self.config_path = os.path.join(config_path, DEFAULT_CONFIG_FILENAME)
        else:
            self.config_dir = os.path.dirname(os.path.abspath(config_path))

        if not os.path.isfile(self.config_path):
            logging.error(
                "PartCAD configuration file is not found: '%s'" % self.config_path
            )
            return

        if self.config_path.endswith(".yaml"):
            self.config_obj = yaml.safe_load(open(self.config_path, "r"))
        if self.config_path.endswith(".json"):
            self.config_obj = json.load(open(self.config_path, "r"))

        # option: "partcad"
        # description: the version of PartCAD required to handle this package
        # values: string initializer for packaging.specifiers.SpecifierSet
        # default: None
        if "partcad" in self.config_obj:
            partcad_requirements = SpecifierSet(self.config_obj["partcad"])
            partcad_version = pkg_resources.get_distribution("partcad").version
            if partcad_version not in partcad_requirements:
                # TODO(clairbee): add better error and exception handling
                raise Exception(
                    "ERROR: Incompatible PartCAD version! %s does not satisfy %s"
                    % (partcad_version, partcad_requirements)
                )

        # option: "pythonVersion"
        # description: the version of python to use in sandboxed environments if any
        # values: string
        # default: "3.10"
        if "pythonVersion" == self.config_obj:
            self.python_version = self.config_obj["pythonVersion"]
        else:
            self.python_version = "3.10"
