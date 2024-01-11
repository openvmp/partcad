#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc


def test_runtime_python_version_3_7():
    ctx = pc.Context("partcad/tests")
    runtime = ctx.get_python_runtime("3.7")
    version_string, errors = runtime.run(["--version"])
    assert errors == ""
    assert version_string.startswith("Python 3.7")


def test_runtime_python_version_3_10():
    ctx = pc.Context("partcad/tests")
    runtime = ctx.get_python_runtime("3.10")
    version_string, errors = runtime.run(["--version"])
    assert errors == ""
    assert version_string.startswith("Python 3.10")


def test_runtime_python_version_3_11():
    ctx = pc.Context("partcad/tests")
    runtime = ctx.get_python_runtime("3.11")
    version_string, errors = runtime.run(["--version"])
    assert errors == ""
    assert version_string.startswith("Python 3.11")
