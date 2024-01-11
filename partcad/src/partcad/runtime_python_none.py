#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.

import os

from . import runtime_python


class NonePythonRuntime(runtime_python.PythonRuntime):
    def __init__(self, ctx, version="3.10"):
        super().__init__(ctx, "none", version)

        if not self.initialized:
            os.makedirs(self.path)
            self.initialized = True

    def run(self, cmd, stdin=""):
        return super().run(["python" + self.version] + cmd, stdin)
