#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.
#

from . import part_factory_file as pff


class PartFactoryPython(pff.PartFactoryFile):
    def __init__(self, ctx, project, part_config):
        super().__init__(ctx, project, part_config, extension=".py")

        self.runtime = self.ctx.get_python_runtime(self.project.python_version)
        self.runtime.prepare_for_package(project)
