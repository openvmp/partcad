#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc


def cli_help_install(subparsers):
    parser_install = subparsers.add_parser(
        "install",
        help="Download and prepare all imported packages",
    )


def cli_install(args):
    if not args.config_path is None:
        pc.init(args.config_path)
    else:
        pc.init()
