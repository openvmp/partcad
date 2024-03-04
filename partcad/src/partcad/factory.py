#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-02-19
#
# Licensed under Apache License, Version 2.0.
#

from . import logging as pc_logging


class Factory:
    def __init__(self) -> None:
        pass


all = {
    "assembly": {},
    "part": {},
}


def register(kind: str, t: str, factory_class: Factory.__class__):
    all[kind][t] = factory_class


def instantiate(kind: str, ctx, project, config):
    t = config["type"]
    if t in all[kind]:
        all[kind][t](ctx, project, config)
    else:
        pc_logging.error("Invalid %s type encountered: %s" % (kind, config))
