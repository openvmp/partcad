#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-04-20
#
# Licensed under Apache License, Version 2.0.
#

from .sketch_factory_file import SketchFactoryFile
from .runtime_python import PythonRuntime


# TODO(clairbee): create ShapeFactoryPython to be reused
#                 by corresponding Sketch, Part and Assembly factories
class SketchFactoryPython(SketchFactoryFile):
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
        before instantiating the sketch.
        """

        # Install dependencies of this package
        await self.runtime.prepare_for_package(self.project)
        await self.runtime.prepare_for_shape(self.config)

    def info(self, sketch):
        info: dict[str, object] = sketch.shape_info()
        info.update(
            {
                "runtime_version": self.runtime.version,
                "runtime_path": self.runtime.path,
            }
        )
        return info

    async def instantiate(self, sketch):
        await super().instantiate(sketch)
