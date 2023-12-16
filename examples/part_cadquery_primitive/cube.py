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

shape = cq.Workplane("front").box(1.0, 1.0, 1.0)
show_object(shape)
# TODO(clairbee): add a wrapper for 'atexit' to 'cadquery' to enable the below
# part = pc.Part(shape=shape)
# pc.finalize(part)
