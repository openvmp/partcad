#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import asyncio
import math
import typing

from .shape_ai import ShapeWithAi
from . import sync_threads as pc_thread
from . import logging as pc_logging


class Part(ShapeWithAi):
    path: typing.Optional[str] = None
    desc: typing.Optional[str] = None
    vendor: typing.Optional[str] = None
    sku: typing.Optional[str] = None
    url: typing.Optional[str] = None
    count_per_sku: int = None
    count: int = None

    errors: list[str] = []

    def __init__(self, config: object = {}, shape=None):
        super().__init__(config)

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

    async def get_shape(self):
        async with self.lock:
            if self.shape is None:
                self.shape = await pc_thread.run_async(self.instantiate, self)
            return self.shape

    def ref_inc(self):
        # TODO(clairbee): add a thread lock here
        self.count += 1

    def clone(self):
        cloned = Part(self.name, self.config, self.shape)
        cloned.count = self.count
        return cloned

    def error(self, msg: str):
        mute = self.config.get("mute", False)
        if mute:
            self.errors.append(msg)
        else:
            pc_logging.error(msg)

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
