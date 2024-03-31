#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.
#

# This script is executed within the python sandbox environment (python runtime)
# to invoke `cadquery` scripts.

import os
import sys

from cadquery import cqgi

sys.path.append(os.path.dirname(__file__))
import wrapper_common


def process(path, request):
    build_parameters = {}
    if "build_parameters" in request:
        build_parameters = request["build_parameters"]

    script = open(path, "r").read()
    if "import partcad" in script:
        script = (
            "import logging\nlogging.basicConfig(level=60)\n"  # Disable PartCAD logging
            + script
        )
    script_object = cqgi.parse(script)
    result = script_object.build(build_parameters=build_parameters)

    if not result.success:
        sys.stderr.write("Exception: ")
        sys.stderr.write(str(result.exception))

    shape = None if not result.first_result else result.first_result.shape
    if hasattr(shape, "val"):
        shape = shape.val()
    if hasattr(shape, "toCompound"):
        shape = shape.toCompound()
    if hasattr(shape, "wrapped"):
        shape = shape.wrapped

    return {
        "success": result.success,
        "exception": result.exception,
        "shape": shape,
    }


path, request = wrapper_common.handle_input()

# Call CadQuery
model = process(path, request)

wrapper_common.handle_output(model)
