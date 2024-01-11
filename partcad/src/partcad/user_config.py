#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.

import logging
import os
import shutil
import yaml


class UserConfig:
    def __init__(self):
        self.config_obj = {}

        config_path = os.getenv("HOME", "/tmp") + "/.partcad/config.yaml"
        if os.path.exists(config_path):
            try:
                self.config_obj = yaml.safe_load(open(config_path, "r"))
            except Exception as e:
                logging.error("ERROR: Failed to parse %s" % config_path)

        # option: pythonSandbox
        # description: sandboxing environment for invoking python scripts
        # values: [none | pypy | conda]
        # default: conda
        if not shutil.which("conda") is None:
            self.python_runtime = "conda"
        else:
            self.python_runtime = "none"

        if "pythonSandbox" in self.config_obj:
            self.python_runtime = self.config_obj["pythonSandbox"]


user_config = UserConfig()
