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
    parser_render.add_argument(
        "-p",
        help="Create the neccessary directory structure if it is missing",
        dest="create_dirs",
        action="store_true",
    )
    parser_render.add_argument(
        "-O",
        help="Create artifacts in the given output directory",
        dest="output_dir",
        type=str,
        nargs="?",
    )
    parser_render.add_argument(
        "-t",
        help="The object is an assembly",
        dest="format",
        type=str,
        nargs="?",
        choices=["svg", "png", "step", "stl", "3mf", "threejs", "obj"],
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

    ctx.option_create_dirs = args.create_dirs

    if args.package is None:
        package = "this"
    else:
        package = args.package

    if args.object is None:
        # Render all parts and assemblies configured to be auto-rendered in this project
        ctx.render(format=args.format, output_dir=args.output_dir)
    else:
        # Render the requested part or assembly
        parts = []
        assemblies = []
        if args.assembly:
            assemblies.append(args.object)
        else:
            parts.append(args.object)

        prj = ctx.get_project(package)
        prj.render(
            parts=parts,
            assemblies=assemblies,
            format=args.format,
            output_dir=args.output_dir,
        )
