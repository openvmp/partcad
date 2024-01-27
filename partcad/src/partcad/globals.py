#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-20
#
# Licensed under Apache License, Version 2.0.

import logging
import os
import shutil

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


def get_assembly(assembly_name, project_name=consts.THIS, params=None) -> Assembly:
    """Get the assembly from the given project"""
    if project_name is None:
        project_name = consts.THIS
    return init().get_assembly(assembly_name, project_name, params=params)


def get_part(part_name, project_name=consts.THIS, params=None) -> Part:
    """Get the part from the given project"""
    if project_name is None:
        project_name = consts.THIS
    return init().get_part(part_name, project_name, params=params)


def finalize(shape, show_object_fn):
    return init().finalize(shape, show_object_fn)


def finalize_real():
    return init()._finalize_real()


def render(format=None, output_dir=None):
    return init().render(format, output_dir)


def create_package(dst_path=consts.DEFAULT_PACKAGE_CONFIG, private=False):
    if private:
        template_name = "init-private.yaml"
    else:
        template_name = "init-public.yaml"
    src_path = os.path.join(os.path.dirname(__file__), "template", template_name)

    if os.path.exists(dst_path):
        return False
    shutil.copyfile(src_path, dst_path)

    return True
