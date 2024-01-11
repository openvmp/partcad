#
# OpenVMP, 2023-2024
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

import argparse

import partcad as pc


def cli_help_render(subparsers: argparse.ArgumentParser):
    parser_render = subparsers.add_parser(
        "render",
        help="Render the selected or all parts, assemblies and scenes in this package",
    )
    group_type = parser_render.add_mutually_exclusive_group(required=False)
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

    parser_render.add_argument(
        "object",
        help="Part (default), assembly or scene to render",
        type=str,
        nargs="?",
    )
    # TODO(clairbee): make the package argument depending on the object argument
    #                 [<object> [<package>]]
    #                 instead of
    #                 [<object>] [<package>]
    parser_render.add_argument(
        "package",
        help="Package to retrieve the object from",
        type=str,
        nargs="?",
    )


def cli_render(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()

    if args.package is None:
        package = "this"
    else:
        package = args.package

    if args.object is None:
        # Render all parts and assemblies configured to be auto-rendered in this project
        ctx.render()
    else:
        # Render the requested part or assembly
        parts = []
        assemblies = []
        if args.assembly:
            assemblies.append(args.object)
        else:
            parts.append(args.object)

        prj = ctx.get_project(package)
        prj.render(parts=parts, assemblies=assemblies)
