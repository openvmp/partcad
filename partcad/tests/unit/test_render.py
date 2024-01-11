#!/usr/bin/env python3
#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-01-06
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc


def test_render_svg_part_1():
    """Render a primitive shape to SVG"""
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    cube = ctx.get_part("cube", "example_part_cadquery_primitive")
    assert cube is not None
    try:
        cube.render_svg()
    except Exception as e:
        assert False, "Valid render request caused an exception: %s" % e


def test_render_svg_assy_1():
    """Render a primitive shape to SVG"""
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    assy = ctx.get_assembly("logo", "example_assembly_assy")
    assert assy is not None
    try:
        assy.render_svg()
    except Exception as e:
        assert False, "Valid render request caused an exception: %s" % e


def test_render_svg_assy_2():
    """Render a primitive shape to SVG"""
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    assy = ctx.get_assembly("logo_embedded", "example_assembly_assy")
    assert assy is not None
    try:
        assy.render_svg()
    except Exception as e:
        assert False, "Valid render request caused an exception: %s" % e
