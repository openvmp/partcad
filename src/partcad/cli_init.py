#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

import os
import shutil
import sys

import partcad as pc


def cli_help_init(subparsers):
    parser_init = subparsers.add_parser(
        "init",
        help="Initialize new PartCAD package in this directory",
    )
    parser_init.add_argument(
        "-p",
        help="Initialize this package as private",
        dest="private",
        action="store_true",
    )


def cli_init(args):
    if os.path.exists("partcad.yaml"):
        print("ERROR: partcad.yaml already exists!")
        sys.exit(1)

    if args.private:
        template_name = "init-private.yaml"
    else:
        template_name = "init-public.yaml"
    template_path = os.path.join(os.path.dirname(__file__), "template", template_name)
    shutil.copyfile(template_path, "partcad.yaml")
