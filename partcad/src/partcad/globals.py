#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-20
#
# Licensed under Apache License, Version 2.0.

import logging

from .context import Context
from .assembly import Assembly
from .part import Part
from . import consts

global _partcad_context
_partcad_context = None


def init(config_path=".") -> Context:
    """Initialize the default context explicitly using the desired path."""
    global _partcad_context
    global _partcad_context_path

    if _partcad_context is None:
        # logging.debug("Initializing (%s)..." % __name__)

        _partcad_context = Context(config_path)
        _partcad_context_path = config_path
    else:
        if _partcad_context_path != config_path:
            logging.error("Multiple context configurations")
            raise Exception("partcad: multiple context configurations")

    return _partcad_context


def get_assembly(assembly_name, project_name=consts.THIS) -> Assembly:
    """Get the assembly from the given project"""
    if project_name is None:
        project_name = consts.THIS
    return init().get_assembly(assembly_name, project_name)


def get_part(part_name, project_name=consts.THIS) -> Part:
    """Get the part from the given project"""
    if project_name is None:
        project_name = consts.THIS
    return init().get_part(part_name, project_name)


def finalize(shape, show_object_fn):
    return init().finalize(shape, show_object_fn)


def finalize_real():
    return init()._finalize_real()


def render(format=None, output_dir=None):
    return init().render(format, output_dir)
