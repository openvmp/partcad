#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-02-19
#
# Licensed under Apache License, Version 2.0.
#

from . import factory

from . import factory
from .file_factory import FileFactory
from .shape import Shape


class ShapeFactory(factory.Factory):
    fileFactory: FileFactory

    def __init__(self, ctx, project, config) -> None:
        super().__init__()

        self.ctx = ctx
        self.project = project
        self.config = config

        if "fileFrom" in config:
            self.fileFactory = factory.instantiate(
                "file", config["fileFrom"], ctx, project, config
            )
        else:
            self.fileFactory = None

    def info(self, shape):
        """This is the default implementation of the get_info method for factories."""
        return super(Shape, shape).info(self)
