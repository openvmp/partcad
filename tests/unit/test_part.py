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
    assert bolt.get_wrapped() is not None


def test_part_get_2():
    """Load part from the context by the project and part names"""
    ctx = pc.Context("examples/part_step")
    bolt = ctx.get_part("bolt", "this")
    assert bolt is not None
    assert bolt.get_wrapped() is not None


def test_part_get_3():
    """Instantiate a project by a local import config and load a part"""
    ctx = pc.Context()  # Empty config
    _ = pc.ProjectFactoryLocal(ctx, None, test_config_local)
    cylinder = ctx.get_part("cylinder", "primitive_local")
    assert cylinder is not None
    assert cylinder.get_wrapped() is not None


# Note: The below test fails if there are braking changes in the way parts are
#       declared. Keep it this way so that the braking changes are conciously
#       force pushed.
def test_part_get_4():
    """Instantiate a project by a git import config and load a part"""
    ctx = pc.Context()  # Empty config
    factory = pc.ProjectFactoryGit(ctx, None, test_config_git)
    assert factory.project.path.endswith(test_config_git["relPath"])
    cube = factory.project.get_part("cube")
    assert cube is not None
    assert cube.get_wrapped() is not None


def test_part_lazy_loading():
    """Test for lazy loading of geometry data"""
    ctx = pc.Context()  # Empty config
    _ = pc.ProjectFactoryLocal(ctx, None, test_config_local)
    cylinder = ctx.get_part("cylinder", "primitive_local")
    assert cylinder.shape is None
    assert cylinder.get_wrapped() is not None


def test_part_aliases():
    """Test for part aliases"""
    ctx = pc.Context()  # Empty config
    _ = pc.ProjectFactoryLocal(ctx, None, test_config_local)
    # "box" is an alias for "cube"
    box = ctx.get_part("box", "primitive_local")
    assert box.shape is None
    assert box.get_wrapped() is not None


def test_part_example_cadquery_primitive():
    """Instantiate all parts from the example: part_cadquery_primitive"""
    ctx = pc.init("tests/partcad-examples.yaml")
    cube = ctx.get_part("cube", "example_part_cadquery_primitive")
    assert cube is not None
    cylinder = ctx.get_part("cylinder", "example_part_cadquery_primitive")
    assert cylinder is not None
    assert cylinder.get_wrapped() is not None


def test_part_example_cadquery_logo():
    """Instantiate all parts from the example: part_cadquery_logo"""
    ctx = pc.init("tests/partcad-examples.yaml")
    bone = ctx.get_part("bone", "example_part_cadquery_logo")
    assert bone is not None
    head_half = ctx.get_part("head_half", "example_part_cadquery_logo")
    assert head_half is not None
    assert head_half.get_wrapped() is not None


def test_part_example_build123d_primitive():
    """Instantiate all parts from the example: part_build123d_primitive"""
    ctx = pc.init("tests/partcad-examples.yaml")
    cube = ctx.get_part("cube", "example_part_build123d_primitive")
    assert cube is not None
    assert cube.get_wrapped() is not None
