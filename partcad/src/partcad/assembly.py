#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import asyncio
import copy
import typing

import build123d as b3d

from . import shape
from . import sync_threads as pc_thread


class AssemblyChild:
    def __init__(self, item, name=None, location=None):
        self.item = item
        self.name = name
        self.location = location


class Assembly(shape.Shape):
    path: typing.Optional[str] = None

    def __init__(self, config={}):
        super().__init__(config)

        self.desc = None
        if "location" in config:
            self.location = config["location"]
        else:
            self.location = None
        self.shape = None
        self.lock = asyncio.Lock()

        # self.children contains all child parts and assemblies before they turn into 'self.shape'
        self.children = []

        # TODO(clairbee): add reference counter to assemblies
        self.count = 0

    async def do_instantiate(self):
        async with self.lock:
            if len(self.children) == 0:
                self.shape = None  # Invalidate if any
                await pc_thread.run(self.instantiate, self)
                if self.shape is None and len(self.children) == 0:
                    raise Exception("The assembly is empty")

    # add is a non-thread-safe method for end users to create custom Assemblies
    def add(
        self,
        child_item: shape.Shape,  # pc.Part or pc.Assembly
        name=None,
        loc=b3d.Location((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.0),
    ):
        self.children.append(AssemblyChild(child_item, name, loc))

        # Keep part reference counter for bill-of-materials purposes
        child_item.ref_inc()

        self.shape = None  # Invalidate if any

    async def ref_inc_async(self):
        async with self.lock:
            for child in self.children:
                await child.item.ref_inc_async()

    # add is a non-thread-safe method for self.add
    def ref_inc(self):
        for child in self.children:
            child.item.ref_inc()

    async def get_shape(self):
        await self.do_instantiate()
        async with self.lock:
            if self.shape is None:
                child_shapes = []
                tasks = []

                async def per_child(child):
                    item = copy.copy(await child.item.get_build123d())
                    if not child.name is None:
                        item.label = child.name
                    if not child.location is None:
                        item.locate(child.location)
                    return item

                if len(self.children) == 0:
                    raise Exception("The assembly is empty")
                for child in self.children:
                    tasks.append(per_child(child))

                # TODO(clairbee): revisit whether non-determinism here is acceptable
                for f in asyncio.as_completed(tasks):
                    item = await f
                    child_shapes.append(item)

                compound = b3d.Compound(children=child_shapes)
                if not self.name is None:
                    compound.label = self.name
                if not self.location is None:
                    compound.locate(self.location)
                self.shape = compound.wrapped
            if self.shape is None:
                raise Exception("The shape is none")
            return self.shape
            # return copy.copy(
            #     self.shape
            # )  # TODO(clairbee): fix this for the case when the parts are made with cadquery

    async def _render_txt_real(self, file):
        await self.do_instantiate()
        for child in self.children:
            child._render_txt_real(file)

    async def _render_markdown_real(self, file):
        await self.do_instantiate()
        for child in self.children:
            child._render_markdown_real(file)
