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


def test_assembly_primitive1():
    ctx = pc.init("tests/partcad-examples.yaml")
    part1 = ctx.get_part("example_part_cadquery_primitive", "cube")
    assert part1 is not None
    part2 = ctx.get_part("example_part_cadquery_primitive", "cylinder")
    assert part2 is not None

    model = pc.Assembly("example1")
    model.add(part1, loc=pc.Location((0, 0, 0), (0, 0, 1), 0))
    model.add(part2, loc=pc.Location((0, 0, 1), (0, 0, 1), 0))
    ctx.finalize(model)


def test_assembly_example_primitive():
    ctx = pc.init("tests/partcad-examples.yaml")
    assembly = ctx.get_assembly("example_assembly_primitive", "assembly")
    assert assembly is not None


def test_assembly_example_logo():
    ctx = pc.init("tests/partcad-examples.yaml")
    logo = ctx.get_assembly("example_assembly_logo", "logo")
    assert logo is not None
    assert logo.shape is None
    logo.build()
    assert logo.shape is not None
