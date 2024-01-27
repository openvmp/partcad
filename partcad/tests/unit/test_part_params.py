#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-27
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc


def test_part_params_get_1():
    """Load a CadQuery part using parameters"""
    ctx = pc.Context("examples/produce_part_cadquery_primitive")
    brick = ctx.get_part("cube", "this", {"width": 17.0})
    assert brick is not None
    assert brick.get_wrapped() is not None
    assert brick.config["parameters"]["width"]["default"] == 17.0


def test_part_params_get_2():
    """Load a CadQuery part using parameters and type casting"""
    ctx = pc.Context("examples/produce_part_cadquery_primitive")
    brick = ctx.get_part("cube", "this", {"width": "17.0"})
    assert brick is not None
    assert brick.get_wrapped() is not None
    assert brick.config["parameters"]["width"]["default"] == 17.0
