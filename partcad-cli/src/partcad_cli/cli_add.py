#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#


from pathlib import Path

import partcad as pc


def cli_help_add(subparsers):
    parser_add = subparsers.add_parser(
        "add",
        help="Import a package",
    )
    parser_add.add_argument(
        "alias",
        help="Alias to be used to reference the package",
        type=str,
    )
    parser_add.add_argument(
        "location",
        help="Path or URL to the package",
        type=str,
    )

    parser_add_part = subparsers.add_parser(
        "add-part",
        help="Add a part",
    )
    parser_add_part.add_argument(
        "kind",
        help="Type of the part",
        type=str,
        choices=["cadquery", "build123d", "step", "stl", "3mf"],
    )
    parser_add_part.add_argument(
        "path",
        help="Path to the file",
        type=str,
    )

    parser_add_assembly = subparsers.add_parser(
        "add-assembly",
        help="Add a assembly",
    )
    parser_add_assembly.add_argument(
        "kind",
        help="Type of the assembly",
        type=str,
        choices=["assy"],
    )
    parser_add_assembly.add_argument(
        "path",
        help="Path to the file",
        type=str,
    )


def cli_add(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()

    prj = ctx.get_project(pc.THIS)
    prj.add_import(args.alias, args.location)


def cli_add_part(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()

    prj = ctx.get_project(pc.THIS)
    if prj.add_part(args.kind, args.path):
        Path(args.path).touch()


def cli_add_assembly(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()

    prj = ctx.get_project(pc.THIS)
    if prj.add_assembly(args.kind, args.path):
        Path(args.path).touch()
