#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-01
#
# Licensed under Apache License, Version 2.0.
#

# This script contains code shared by all wrapper scripts.

import base64

# import fcntl  # TODO(clairbee): replace it with whatever works on Windows if needed
import os
import pickle
import sys

from cq_serialize import register as register_cq_helper


def handle_input():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s <path>\n" % sys.argv[0])
        sys.exit(1)

    # Handle the input
    # - Comand line parameters
    path = os.path.normpath(sys.argv[1])
    if len(sys.argv) > 2:
        os.chdir(os.path.normpath(sys.argv[2]))
    # - Content passed via stdin
    # #   - Make stdin blocking so that we can read until EOF
    # flag = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    # fcntl.fcntl(sys.stdin, fcntl.F_SETFL, flag & ~os.O_NONBLOCK)
    #   - Read until EOF
    input_str = sys.stdin.read()
    #   - Unpack the content received via stdin

    # TODO(clairbee): is .encode() needed here?
    request_bytes = base64.b64decode(input_str)

    register_cq_helper()
    request = pickle.loads(request_bytes)
    return path, request


def handle_output(model):
    # Serialize the output
    register_cq_helper()
    picklestring = pickle.dumps(model)
    response = base64.b64encode(picklestring)
    print(response.decode())
