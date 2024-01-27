#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

# import argparse
import logging

import partcad as pc


# TODO(clairbee): fix type checking here
# def cli_help_show(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]):
def cli_help_show(subparsers):
    parser_show = subparsers.add_parser(
        "show",
        help="Visualize a part, assembly or scene",
    )
    group_type = parser_show.add_mutually_exclusive_group(required=False)
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

    parser_show.add_argument(
        "-p",
        "--param",
        metavar="<param_name>=<param_value>",
        help="Assign a value to the parameter",
        dest="params",
        action="append",
    )

    parser_show.add_argument(
        "object",
        help="Part (default), assembly or scene to show",
        type=str,
    )
    parser_show.add_argument(
        "package",
        help="Package to retrieve the object from",
        type=str,
        nargs="?",
    )


def cli_show(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()

    if args.package is None:
        package = "this"
    else:
        package = args.package

    params = {}
    if not args.params is None:
        for kv in args.params:
            k, v = kv.split("=")
            params[k] = v

    if args.assembly:
        obj = ctx.get_assembly(args.object, package, params=params)
    else:
        obj = ctx.get_part(args.object, package, params=params)

    if obj is None:
        if args.package is None:
            logging.error("Object %s not found" % args.object)
        else:
            logging.error(
                "Object %s not found in package %s" % (args.object, args.package)
            )
    else:
        obj.show()
