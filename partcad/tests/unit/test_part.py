#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import asyncio
import pytest
import shutil

import partcad as pc

test_config_local = {
    "name": "primitive_local",
    "type": "local",
    "path": "examples/produce_part_cadquery_primitive",
}

test_config_git = {
    "name": "primitive_git",
    "type": "git",
    "url": "https://github.com/openvmp/partcad",
    "relPath": "examples/produce_part_cadquery_primitive",
}


def test_part_get_step_1():
    """Load a STEP part from a project by the part name"""
    ctx = pc.Context("examples/produce_part_step")
    repo1 = ctx.get_project("this")
    bolt = repo1.get_part("bolt")
    assert bolt is not None
    assert bolt.get_wrapped() is not None


def test_part_get_step_2():
    """Load a STEP part from the context by the project and part names"""
    ctx = pc.Context("examples/produce_part_step")
    bolt = ctx._get_part("bolt", "this")
    assert bolt is not None

    wrapped = asyncio.run(bolt.get_wrapped())
    assert wrapped is not None


def test_part_get_stl():
    """Load a STL part"""
    ctx = pc.Context("examples/produce_part_stl")
    part = ctx._get_part("cube", "this")
    assert part is not None

    wrapped = asyncio.run(part.get_wrapped())
    assert wrapped is not None


def test_part_get_3mf():
    """Load a 3MF part"""
    ctx = pc.Context("examples/produce_part_3mf")
    part = ctx._get_part("cube", "this")
    assert part is not None

    wrapped = asyncio.run(part.get_wrapped())
    assert wrapped is not None


def test_part_get_scad():
    """Load an OpenSCAD part"""
    scad_path = shutil.which("openscad")
    if not scad_path is None:
        ctx = pc.Context("examples/produce_part_scad")
        part = ctx._get_part("cube", "this")
        assert part is not None

        wrapped = asyncio.run(part.get_wrapped())
        assert wrapped is not None
    else:
        pytest.skip("No OpenSCAD installed")


def test_part_get_3():
    """Instantiate a project by a local import config and load a part"""
    ctx = pc.Context()  # Empty config
    _ = pc.ProjectFactoryLocal(ctx, None, test_config_local)
    cylinder = ctx._get_part("cylinder", "primitive_local")
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

    wrapped = asyncio.run(cube.get_wrapped())
    assert wrapped is not None


def test_part_lazy_loading():
    """Test for lazy loading of geometry data"""
    ctx = pc.Context()  # Empty config
    _ = pc.ProjectFactoryLocal(ctx, None, test_config_local)
    cylinder = ctx._get_part("cylinder", "primitive_local")
    assert cylinder.shape is None

    wrapped = asyncio.run(cylinder.get_wrapped())
    assert wrapped is not None


def test_part_aliases():
    """Test for part aliases"""
    ctx = pc.Context()  # Empty config
    _ = pc.ProjectFactoryLocal(ctx, None, test_config_local)
    # "box" is an alias for "cube"
    box = ctx._get_part("box", "primitive_local")
    assert box is not None
    assert box.shape is None

    wrapped = asyncio.run(box.get_wrapped())
    assert wrapped is not None


def test_part_example_cadquery_primitive():
    """Instantiate all parts from the example: part_cadquery_primitive"""
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    cube = ctx._get_part("cube", "example_part_cadquery_primitive")
    assert cube is not None
    cylinder = ctx._get_part("cylinder", "example_part_cadquery_primitive")
    assert cylinder is not None

    wrapped = asyncio.run(cylinder.get_wrapped())
    assert wrapped is not None


def test_part_example_cadquery_logo():
    """Instantiate all parts from the example: part_cadquery_logo"""
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    bone = ctx._get_part("bone", "example_part_cadquery_logo")
    assert bone is not None
    head_half = ctx._get_part("head_half", "example_part_cadquery_logo")
    assert head_half is not None

    wrapped = asyncio.run(head_half.get_wrapped())
    assert wrapped is not None


def test_part_example_build123d_primitive():
    """Instantiate all parts from the example: part_build123d_primitive"""
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    cube = ctx._get_part("cube", "example_part_build123d_primitive")
    assert cube is not None

    wrapped = ctx.get_part_shape("cube", "example_part_build123d_primitive")
    assert wrapped is not None
