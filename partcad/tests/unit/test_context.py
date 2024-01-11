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


def test_ctx1():
    ctx = pc.Context("partcad/tests")
    assert ctx is not None
