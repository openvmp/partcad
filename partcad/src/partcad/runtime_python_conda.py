#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.

import os
import shutil
import subprocess

from . import runtime_python


class CondaPythonRuntime(runtime_python.PythonRuntime):
    def __init__(self, ctx, version=None):
        super().__init__(ctx, "conda", version)

        if not self.initialized:
            self.conda_path = shutil.which("conda")
            if self.conda_path is None:
                raise Exception(
                    "ERROR: PartCAD is configured to use conda, but conda is missing"
                )

            try:
                os.makedirs(self.path)
                subprocess.run(
                    [
                        self.conda_path,
                        "create",
                        "-y",
                        "-p",
                        self.path,
                        "python=%s" % version,
                    ]
                )
                subprocess.run(["conda", "install", "-y", "-p", self.path, "pip"])
                self.initialized = True
            except Exception as e:
                shutil.rmtree(self.path)
                raise e

    def run(self, cmd, stdin=""):
        return super().run(
            [
                self.conda_path,
                "run",
                "--no-capture-output",
                "-p",
                self.path,
                # "python",  # Trust conda to set the link correctly
                "python%s" % self.version,  # This doesn't work on Windows
            ]
            + cmd,
            stdin,
        )
