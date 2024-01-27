#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import math
import threading
import typing

from . import shape


class Part(shape.Shape):
    path: typing.Optional[str] = None

    def __init__(self, config: object = {}, shape=None):
        super().__init__(config)

        self.shape = shape
        self.lock = threading.RLock()

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

    def get_shape(self):
        with self.lock:
            if self.shape is None:
                self.instantiate(self)
            return self.shape

    def ref_inc(self):
        self.count += 1

    def clone(self):
        cloned = Part(self.name, self.config, self.shape)
        cloned.count = self.count
        return cloned

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
