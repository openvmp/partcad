#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-26
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc


def test_part_alias_get_1():
    """Load a STEP part using a short form alias"""
    ctx = pc.Context("examples/produce_part_step")
    bolt = ctx.get_part("screw", "this")
    assert bolt is not None
    assert bolt.get_wrapped() is not None


def test_part_alias_get_2():
    """Load a STEP part using a long form alias"""
    ctx = pc.Context("examples/produce_part_step")
    bolt = ctx.get_part("fastener", "this")
    assert bolt is not None
    assert bolt.get_wrapped() is not None


def test_part_alias_get_3():
    """Load a STEP part using a long form alias"""
    ctx = pc.Context("examples/produce_part_step")
    bolt = ctx.get_part("hexhead", "this")
    assert bolt is not None
    assert bolt.get_wrapped() is not None


# Add support for the following one
# def test_part_alias_get_with_params():
#     """Load a CadQuery part using an alias with parameters in its name and see if the parameters changed"""
#     ctx = pc.Context("examples/produce_part_cadquery_primitive")
#     brick = ctx.get_part("brick2", "this")
#     assert brick is not None
#     assert brick.get_wrapped() is not None

#     # Check whether the parameter change is in effect
#     assert brick.config["parameters"]["width"]["default"] == 20.0
