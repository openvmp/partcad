#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.
#

from .part_factory_file import PartFactoryFile
from .runtime_python import PythonRuntime


class PartFactoryPython(PartFactoryFile):
    runtime: PythonRuntime
    cwd: str

    def __init__(
        self, ctx, source_project, target_project, config, can_create=False
    ):
        super().__init__(
            ctx,
            source_project,
            target_project,
            config,
            extension=".py",
            can_create=can_create,
        )
        self.cwd = config.get("cwd", None)
        self.runtime = self.ctx.get_python_runtime(self.project.python_version)

    async def prepare_python(self):
        """
        This method is called by child classes
        to prepare the Python environment
        before instantiating the part.
        """

        # Install dependencies of this package
        await self.runtime.prepare_for_package(self.project)
        await self.runtime.prepare_for_shape(self.config)

    def info(self, part):
        info: dict[str, object] = part.shape_info()
        info.update(
            {
                "runtime_version": self.runtime.version,
                "runtime_path": self.runtime.path,
            }
        )
        return info

    async def instantiate(self, part):
        await super().instantiate(part)
