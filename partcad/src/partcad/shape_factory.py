#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-02-19
#
# Licensed under Apache License, Version 2.0.
#

from . import factory

from .shape import Shape


class ShapeFactory(factory.Factory):
    def __init__(self) -> None:
        super().__init__()

    def info(self, shape):
        """This is the default implementation of the get_info method for factories."""
        return super(Shape, shape).info(self)
