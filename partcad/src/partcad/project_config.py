#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

from jinja2 import Environment, FileSystemLoader
import json
import os
from packaging.specifiers import SpecifierSet
import sys
import yaml

from . import logging as pc_logging

DEFAULT_CONFIG_FILENAME = "partcad.yaml"


class Configuration:
    name: str

    def __init__(self, name, config_path=DEFAULT_CONFIG_FILENAME):
        self.name = name
        self.config_obj = {}
        self.config_dir = config_path
        self.config_path = config_path

        if os.path.isdir(config_path):
            self.config_path = os.path.join(config_path, DEFAULT_CONFIG_FILENAME)
        else:
            self.config_dir = os.path.dirname(os.path.abspath(config_path))

        if not os.path.isfile(self.config_path):
            pc_logging.error(
                "PartCAD configuration file is not found: '%s'" % self.config_path
            )
            return

        # Read the body of the configuration file
        fp = open(self.config_path, "r")
        config = fp.read()
        fp.close()

        # Resolve Jinja templates
        template = Environment(
            loader=FileSystemLoader(self.config_dir + os.path.sep)
        ).from_string(config)
        config = template.render(
            package_name=name,
        )

        # Parse the config
        if self.config_path.endswith(".yaml"):
            self.config_obj = yaml.safe_load(config)
        if self.config_path.endswith(".json"):
            self.config_obj = json.load(config)

        self.config_obj["name"] = name

        if not "render" in self.config_obj or self.config_obj["render"] is None:
            self.config_obj["render"] = {}

        # option: "partcad"
        # description: the version of PartCAD required to handle this package
        # values: string initializer for packaging.specifiers.SpecifierSet
        # default: None
        if "partcad" in self.config_obj:
            partcad_requirements = SpecifierSet(self.config_obj["partcad"])
            partcad_version = sys.modules["partcad"].__version__
            if partcad_version not in partcad_requirements:
                # TODO(clairbee): add better error and exception handling
                raise Exception(
                    "ERROR: Incompatible PartCAD version! %s does not satisfy %s"
                    % (partcad_version, partcad_requirements)
                )

        # option: "pythonVersion"
        # description: the version of python to use in sandboxed environments if any
        # values: string (e.g. "3.10")
        # default: <The major and minor version of the current interpreter>
        if "pythonVersion" == self.config_obj:
            self.python_version = self.config_obj["pythonVersion"]
        else:
            self.python_version = "%d.%d" % (
                sys.version_info.major,
                sys.version_info.minor,
            )
