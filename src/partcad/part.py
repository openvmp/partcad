#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import math
import random
import string
from . import shape

import cadquery as cq


class Part(shape.Shape):
    def __init__(self, name=None, config={}, shape=None):
        if name is None:
            name = "part" + "".join(
                random.choices(string.ascii_uppercase + string.digits, k=8)
            )
        super().__init__(name)

        self.config = config
        if "path" in config:
            self.path = config["path"]
        else:
            # TODO(clairbee): consider autodetecting the root of the project
            #                 that created this Part
            self.path = "."
        self.shape = shape

        self.desc = None
        if "desc" in config:
            self.desc = config["desc"]
        self.vendor = None
        if "vendor" in config:
            self.vendor = config["vendor"]
        self.sku = None
        if "sku" in config:
            self.sku = config["sku"]
        self.url = None
        if "url" in config:
            self.url = config["url"]
        if "count_per_sku" in config:
            self.count_per_sku = config["count_per_sku"]
        else:
            self.count_per_sku = 1
        self.count = 0

    def set_shape(self, shape):
        self.shape = shape

    def ref_inc(self):
        self.count += 1

    def clone(self):
        cloned = Part(self.name, self.path, self.config, self.shape)
        cloned.count = self.count
        return cloned

    def getCompound(self):
        return self.shape
        # shape = self.shape
        # # if not hasattr(shape, "wrapped"):
        # #     cq_solid = cq.Solid.makeBox(1, 1, 1)
        # #     cq_solid.wrapped = shape
        # #     shape = cq_solid
        # if self.compound is None:
        #     # self.compound = cq.Compound.makeCompound(shape)
        #     # self.compound = shape.toCompound()
        #     if hasattr(shape, "toCompound"):
        #         self.compound = shape.toCompound()
        #         if not hasattr(self.compound, "wrapped"):
        #             cq_solid = cq.Solid.makeBox(1, 1, 1)
        #             cq_solid.wrapped = self.compound
        #             self.compound = cq_solid
        #     else:
        #         self.compound = shape
        #     # else:
        #     #     self.compound = cq.Compound.makeCompound(shape.wrapped)
        # else:
        #     self.compound = shape
        # return self.compound

    def _render_txt_real(self, file):
        file.write(self.name + ": " + self.count + "\n")

    def _render_markdown_real(self, file):
        name = self.name
        vendor = ""
        sku = ""
        if not self.desc is None:
            name = self.desc
        if not self.vendor is None:
            vendor = self.vendor
        if not self.sku is None:
            sku = self.sku
        if self.url is None:
            label = name
        else:
            label = "[" + name + "](" + self.url + ")"
            sku = "[" + sku + "](" + self.url + ")"
        count = str(math.ceil(self.count / self.count_per_sku))
        img_url = self._get_svg_url()

        file.write(
            "| "
            + label
            + " | "
            + count
            + " |"
            + vendor
            + " |"
            + sku
            + " |"
            + " !["
            + name
            + "]("
            + img_url
            + ")"
            + " |\n"
        )
