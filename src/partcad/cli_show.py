#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc


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
        pc.init(args.config_path)

    if args.assembly:
        obj = pc.get_assembly(args.object, args.package)
    else:
        obj = pc.get_part(args.object, args.package)
    obj.show()
