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
    def __init__(self, ctx, version="3.10"):
        super().__init__(ctx, "conda", version)

        if not self.initialized:
            if shutil.which("conda") is None:
                raise Exception(
                    "ERROR: PartCAD is configured to use missing conda to execute Python scripts (CadQuery, build123d etc)"
                )

            try:
                os.makedirs(self.path)
                subprocess.run(
                    ["conda", "create", "-y", "-p", self.path, "python=%s" % version]
                )
                subprocess.run(["conda", "install", "-y", "-p", self.path, "pip"])
                self.initialized = True
            except Exception as e:
                shutil.rmtree(self.path)
                raise e

    def run(self, cmd, stdin=""):
        return super().run(
            [
                "conda",
                "run",
                "--no-capture-output",
                "-p",
                self.path,
                "python%s" % self.version,
            ]
            + cmd,
            stdin,
        )
