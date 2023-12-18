#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-09-30
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc

if __name__ != "__cqgi__":
    from cq_server.ui import ui, show_object

bolt = pc.get_part("example_part_step", "bolt")
bone = pc.get_part("example_part_cadquery_logo", "bone")
head_half = pc.get_part("example_part_cadquery_logo", "head_half")

model = pc.Assembly()
model.add(bone, loc=pc.Location((0, 0, 0), (0, 0, 1), 0))
model.add(bone, loc=pc.Location((0, 0, -2.5), (0, 0, 1), -90))
model.add(head_half, "head_half_1", pc.Location((0, 0, 27.5), (0, 0, 1), 0))
model.add(head_half, "head_half_2", pc.Location((0, 0, 25), (0, 0, 1), -90))
model.add(bolt, loc=pc.Location((0, 0, 7.5), (0, 0, 1), 0))
pc.finalize(model, show_object)
