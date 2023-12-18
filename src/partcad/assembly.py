#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import random
import string

import cadquery as cq

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
        self.shape = cq.Assembly(name=self.name)

        # self.children contains all child parts and assemblies
        self.children = {}

    def add(
        self,
        child,  # pc.Part or pc.Assembly
        name=None,
        loc=cq.Location((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.0),
    ):
        self.shape = self.shape.add(child.shape, name=name, loc=loc)
        child.ref_inc()

    def ref_inc(self):
        for child in self.children:
            child.ref_inc()

    def _export_txt_real(self, file):
        for child in self.children:
            child._export_txt_real(file)

    def _export_markdown_real(self, file):
        for child in self.children:
            child._export_markdown_real(file)
