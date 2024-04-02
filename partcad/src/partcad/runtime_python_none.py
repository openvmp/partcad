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
    def __init__(self, ctx, version=None):
        super().__init__(ctx, "none", version)

        if not self.initialized:
            os.makedirs(self.path)
            self.initialized = True

    async def run(self, cmd, stdin=""):
        return await super().run(
            [
                "python" if os.name != "nt" else "pythonw",
                # "python%s" % self.version, # This doesn't work on Windows
            ]
            + cmd,
            stdin,
        )
