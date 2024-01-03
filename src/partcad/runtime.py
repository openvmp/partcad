#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.

import os


class Runtime:
    def __init__(self, ctx, name):
        self.ctx = ctx
        self.name = name
        self.path = os.getenv("HOME", "/tmp") + "/.partcad/runtime/partcad-" + name
        self.initialized = os.path.exists(self.path)
