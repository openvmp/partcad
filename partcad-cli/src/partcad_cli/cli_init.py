#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

import logging
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
    if args.private:
        template_name = "init-private.yaml"
    else:
        template_name = "init-public.yaml"
    src_path = os.path.join(os.path.dirname(__file__), "template", template_name)

    if not args.config_path is None:
        if os.path.isdir(args.config_path):
            dst_path = os.path.join(args.config_path, "partcad.yaml")
        else:
            dst_path = args.config_path
    else:
        dst_path = "partcad.yaml"

    if os.path.exists(dst_path):
        logging.error("'%s' already exists!" % dst_path)
        sys.exit(1)
    shutil.copyfile(src_path, dst_path)
