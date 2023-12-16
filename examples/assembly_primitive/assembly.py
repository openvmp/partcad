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

part1 = pc.get_part("example_part_cadquery_primitive", "cube")
part2 = pc.get_part("example_part_cadquery_primitive", "cylinder")

model = pc.Assembly()
model.add(part1, loc=pc.Location((0, 0, 0), (0, 0, 1), 0))
model.add(part2, loc=pc.Location((0, 0, 10), (0, 0, 1), 0))
pc.finalize(model)
