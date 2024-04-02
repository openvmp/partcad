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

import cadquery as cq

sys.path.append(os.path.dirname(__file__))
import wrapper_common


def process(path, request):
    shape = cq.importers.importStep(path).val().wrapped

    return {
        "success": True,
        "exception": None,
        "shape": shape,
    }


path, request = wrapper_common.handle_input()

# Call CadQuery
model = process(path, request)

wrapper_common.handle_output(model)
