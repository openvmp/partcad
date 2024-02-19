#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#


def cli_help_install(subparsers):
    parser_install = subparsers.add_parser(
        "install",
        help="Download and prepare all imported packages",
    )
    parser_update = subparsers.add_parser(
        "update",
        help="Update all imported packages",
    )


def cli_install(args, ctx):
    # No op.
    # The context initialization that is done in cli.py is doing everything
    # necessary already.
    _ignore = True
