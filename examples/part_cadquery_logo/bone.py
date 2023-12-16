#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-09-30
#
# Licensed under Apache License, Version 2.0.
#

import cadquery as cq

shape = cq.Workplane("front").box(100.0, 20.0, 2.5)
show_object(shape)
