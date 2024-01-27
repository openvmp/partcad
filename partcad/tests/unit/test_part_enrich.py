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


def test_part_enrich_get_1():
    """Load a CadQuery part using enrichment for parameters"""
    ctx = pc.Context("examples/produce_part_cadquery_primitive")
    brick = ctx.get_part("brick", "this")
    assert brick is not None
    assert brick.get_wrapped() is not None
