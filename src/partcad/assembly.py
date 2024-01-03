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
        self.shape = None

        # self.children contains all child parts and assemblies
        self.children = []

        # TODO(clairbee): add reference counter to assemblies
        self.count = 0

    def add(
        self,
        child: shape.Shape,  # pc.Part or pc.Assembly
        name=None,
        loc=b3d.Location((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.0),
    ):
        child_item = copy.copy(child.get_build123d()).locate(loc)  # Shallow copy
        # child_item.label = name # TODO(clairbee): fix this
        self.children.append(child_item)

        # Keep part reference counter for bill-of-materials purposes
        child.ref_inc()

        # Destroy the previous object if any
        self.shape = None

    def ref_inc(self):
        for child in self.children:
            child.ref_inc()

    def get_shape(self):
        if self.shape is None:
            self.shape = b3d.Compound(label=self.name, children=self.children)
        return self.shape

    def get_build123d(self):
        return copy.copy(self.get_shape())

    def get_wrapped(self):
        return self.get_shape()

    def _render_txt_real(self, file):
        for child in self.children:
            child._render_txt_real(file)

    def _render_markdown_real(self, file):
        for child in self.children:
            child._render_markdown_real(file)
