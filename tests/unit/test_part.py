#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc

test_config_local = {
    "name": "primitive_local",
    "type": "local",
    "path": "examples/part_cadquery_primitive",
}

test_config_git = {
    "name": "primitive_git",
    "type": "git",
    "url": "https://github.com/openvmp/partcad",
    "relPath": "examples/part_cadquery_primitive",
}


def test_part_get_1():
    """Load part from a project by the part name"""
    ctx = pc.Context("examples/part_step")
    repo1 = ctx.get_project("this")
    bolt = repo1.get_part("bolt")
    assert bolt is not None


def test_part_get_2():
    """Load part from the context by the project and part names"""
    ctx = pc.Context("examples/part_step")
    bolt = ctx.get_part("this", "bolt")
    assert bolt is not None


def test_part_get_3():
    """Instantiate a project by a local import config and load a part"""
    ctx = pc.Context()  # Empty config
    _ = pc.ProjectFactoryLocal(ctx, None, test_config_local)
    cylinder = ctx.get_part("primitive_local", "cylinder")
    assert cylinder is not None


def test_part_get_4():
    """Instantiate a project by a git import config and load a part"""
    ctx = pc.Context()  # Emplty config
    factory = pc.ProjectFactoryGit(ctx, None, test_config_git)
    cube = factory.project.get_part("cube")
    assert cube is not None


def test_part_example_primitive():
    """Instantiate all parts from the example: part_cadquery_primitive"""
    ctx = pc.init("tests/partcad-examples.yaml")
    cube = ctx.get_part("example_part_cadquery_primitive", "cube")
    assert cube is not None
    cylinder = ctx.get_part("example_part_cadquery_primitive", "cylinder")
    assert cylinder is not None


def test_part_example_logo():
    """Instantiate all parts from the example: part_cadquery_logo"""
    ctx = pc.init("tests/partcad-examples.yaml")
    bone = ctx.get_part("example_part_cadquery_logo", "bone")
    assert bone is not None
    head_half = ctx.get_part("example_part_cadquery_logo", "head_half")
    assert head_half is not None
