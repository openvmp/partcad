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
import cadquery as cq

if __name__ != "__cqgi__":
    from cq_server.ui import ui, show_object

shape = cq.Workplane("front").box(10.0, 10.0, 10.0)

# This example demonstrates that partcad is compatible with CQGI.

# show_object(shape)
part = pc.Part(shape=shape)
pc.finalize(part, show_object)
