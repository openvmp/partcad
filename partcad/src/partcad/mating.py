#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-04-20
#
# Licensed under Apache License, Version 2.0.
#

from .interface import Interface


class Mating:
    """A mating between two interfaces."""

    source: Interface
    target: Interface
    desc: str
    count: int

    def __init__(
        self,
        source: Interface,
        target: Interface,
        config: dict = {},
        reverse: bool = False,
    ):
        self.source = source
        self.target = target
        self.desc = config["desc"] if "desc" in config else ""
        self.count = 0
