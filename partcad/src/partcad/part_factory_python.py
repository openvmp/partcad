#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.
#

from . import part_factory_file as pff
from .runtime_python import PythonRuntime


class PartFactoryPython(pff.PartFactoryFile):
    runtime: PythonRuntime

    def __init__(
        self, ctx, source_project, target_project, part_config, can_create=False
    ):
        super().__init__(
            ctx,
            source_project,
            target_project,
            part_config,
            extension=".py",
            can_create=can_create,
        )

        self.runtime = self.ctx.get_python_runtime(self.project.python_version)

    async def prepare_python(self):
        """
        This method is called by child classes
        to prepare the Python environment
        before instantiating the part.
        """
        await self.runtime.prepare_for_package(self.project)
