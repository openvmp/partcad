#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc


def cli_help_render(subparsers):
    parser_render = subparsers.add_parser(
        "render",
        help="Render parts, assemblies and scenes in this package",
    )


def cli_render(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()

    ctx.render()
