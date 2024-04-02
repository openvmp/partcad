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
from . import logging as pc_logging


class CondaPythonRuntime(runtime_python.PythonRuntime):
    def __init__(self, ctx, version=None):
        super().__init__(ctx, "conda", version)

        self.conda_path = shutil.which("conda")

    async def run(self, cmd, stdin=""):
        with self.lock:
            if not self.initialized:
                with pc_logging.Action("Conda", "create", self.version):
                    if self.conda_path is None:
                        raise Exception(
                            "ERROR: PartCAD is configured to use conda, but conda is missing"
                        )

                    try:
                        os.makedirs(self.path)

                        # Install new conda environment with the preferred Python version
                        p = subprocess.Popen(
                            [
                                self.conda_path,
                                "create",
                                "-y",
                                "-q",
                                "--json",
                                "-p",
                                self.path,
                                "python=%s" % self.version,
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        _, stderr = p.communicate()
                        if not stderr is None and stderr != b"":
                            pc_logging.error(
                                "conda env install error: %s" % stderr
                            )

                        # Install pip into the newly created conda environment
                        p = subprocess.Popen(
                            [
                                self.conda_path,
                                "install",
                                "-y",
                                "-q",
                                "--json",
                                "-p",
                                self.path,
                                "pip",
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        _, stderr = p.communicate()
                        if not stderr is None and stderr != b"":
                            pc_logging.error(
                                "conda pip install error: %s" % stderr
                            )

                        self.initialized = True
                    except Exception as e:
                        shutil.rmtree(self.path)
                        raise e

        return await super().run(
            [
                self.conda_path,
                "run",
                "--no-capture-output",
                "-p",
                self.path,
                "python" if os.name != "nt" else "pythonw",
                # "python%s" % self.version,  # This doesn't work on Windows
            ]
            + cmd,
            stdin,
        )
