#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import copy
import random
import string

import build123d as b3d

from . import shape


class AssemblyChild:
    def __init__(self, item, name=None, location=None):
        self.item = item
        self.name = name
        self.location = location


class Assembly(shape.Shape):
    def __init__(self, name=None, config={}):
        super().__init__(name)

        self.config = config
        if name is None:
            self.name = "assembly_" + "".join(
                random.choice(string.ascii_uppercase + string.digits) for _ in range(6)
            )
        else:
            self.name = name
        if "location" in config:
            self.location = config["location"]
        else:
            self.location = None
        self.shape = None

        # self.children contains all child parts and assemblies
        self.children = []

        # TODO(clairbee): add reference counter to assemblies
        self.count = 0

    def add(
        self,
        child_item: shape.Shape,  # pc.Part or pc.Assembly
        name=None,
        loc=b3d.Location((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.0),
    ):
        self.children.append(AssemblyChild(child_item, name, loc))

        # Keep part reference counter for bill-of-materials purposes
        child_item.ref_inc()

        # Destroy the previous object if any
        self.shape = None

    def ref_inc(self):
        for child in self.children:
            child.item.ref_inc()

    def get_shape(self):
        if self.shape is None:
            child_shapes = []
            for child in self.children:
                item = copy.copy(child.item.get_build123d())
                if not child.name is None:
                    item.label = child.name
                if not item.location is None:
                    item.locate(child.location)
                child_shapes.append(item)
            shape = b3d.Compound(children=child_shapes)
            if not self.name is None:
                shape.label = self.name
            if not self.location is None:
                shape.locate(self.location)
            self.shape = shape.wrapped
        return copy.copy(self.shape)

    def get_wrapped(self):
        return self.get_shape()

    def _render_txt_real(self, file):
        for child in self.children:
            child._render_txt_real(file)

    def _render_markdown_real(self, file):
        for child in self.children:
            child._render_markdown_real(file)
