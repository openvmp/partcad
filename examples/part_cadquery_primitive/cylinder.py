#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import cadquery as cq

shape = cq.Workplane("front").circle(1.0).extrude(1.0)
show_object(shape)
