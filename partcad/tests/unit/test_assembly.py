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


def test_assembly_primitive():
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    part1 = ctx.get_part("cube", "example_part_cadquery_primitive")
    assert part1 is not None
    part2 = ctx.get_part("cylinder", "example_part_cadquery_primitive")
    assert part2 is not None

    model = pc.Assembly("example1")
    model.add(part1, loc=pc.Location((0, 0, 0), (0, 0, 1), 0))
    model.add(part2, loc=pc.Location((0, 0, 1), (0, 0, 1), 0))
    ctx.finalize(model, None)


def test_assembly_example_assy_primitive():
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    primitive = ctx.get_assembly("primitive", "example_assembly_assy")
    assert primitive is not None
    assert primitive.get_cadquery() is not None
    assert primitive.get_build123d() is not None
    assert primitive.get_shape() is not None


def test_assembly_example_assy_logo():
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    logo = ctx.get_assembly("logo", "example_assembly_assy")
    assert logo is not None
    assert logo.get_cadquery() is not None
    assert logo.get_build123d() is not None
    assert logo.get_shape() is not None


def test_assembly_example_assy_logo_embedded():
    ctx = pc.init("partcad/tests/partcad-examples.yaml")
    logo = ctx.get_assembly("logo_embedded", "example_assembly_assy")
    assert logo is not None
    assert logo.get_cadquery() is not None
    assert logo.get_build123d() is not None
    assert logo.get_shape() is not None
