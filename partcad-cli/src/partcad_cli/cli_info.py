#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-23
#
# Licensed under Apache License, Version 2.0.
#

import logging
from pprint import pprint

import partcad as pc
from partcad.utils import total_size


def cli_help_info(subparsers):
    parser_info = subparsers.add_parser(
        "info",
        help="Show detailed info a part, assembly or scene",
    )
    group_type = parser_info.add_mutually_exclusive_group(required=False)
    group_type.add_argument(
        "-a",
        help="The object is an assembly",
        dest="assembly",
        action="store_true",
    )
    group_type.add_argument(
        "-s",
        help="The object is a scene",
        dest="scene",
        action="store_true",
    )

    parser_info.add_argument(
        "object",
        help="Part (default), assembly or scene to show",
        type=str,
    )
    parser_info.add_argument(
        "package",
        help="Package to retrieve the object from",
        type=str,
        nargs="?",
    )


def cli_info(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()

    if args.package is None:
        package = "this"
    else:
        package = args.package

    if args.assembly:
        obj = ctx.get_assembly(args.object, package)
    else:
        obj = ctx.get_part(args.object, package)

    if obj is None:
        if args.package is None:
            logging.error("Object %s not found" % args.object)
        else:
            logging.error(
                "Object %s not found in package %s" % (args.object, args.package)
            )
    else:
        print("CONFIGURATION:")
        pprint(obj.config)
        print()
        print("RUNTIME PROPERTIES:")
        obj.get_shape()
        print("Memory: %d KB" % ((total_size(obj) + 1023) / 1024))
