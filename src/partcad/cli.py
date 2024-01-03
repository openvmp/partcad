#!/usr/bin/env python
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-22
#
# Licensed under Apache License, Version 2.0.
#

import argparse
import logging

import partcad as pc

from .cli_add import *
from .cli_init import *
from .cli_install import *
from .cli_list import *
from .cli_render import *
from .cli_show import *


def main():
    parser = argparse.ArgumentParser(
        description="PartCAD command line tool",
    )
    parser.add_argument(
        "-p",
        help="Package path (a YAML file or a directory with 'partcad.yaml')",
        type=str,
        default=None,
        dest="config_path",
    )
    # TODO(clairbee): add a config option to change logging mechanism and level
    subparsers = parser.add_subparsers(dest="command")
    cli_help_add(subparsers)
    cli_help_init(subparsers)
    cli_help_install(subparsers)
    cli_help_list(subparsers)
    cli_help_render(subparsers)
    cli_help_show(subparsers)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.command == "add":
        cli_add(args)

    elif args.command == "init":
        cli_init(args)

    elif args.command == "install":
        cli_install(args)

    elif args.command == "list":
        cli_list(args)

    elif args.command == "list-all":
        cli_list_assemblies(args)
        cli_list_parts(args)

    elif args.command == "list-parts":
        cli_list_parts(args)

    elif args.command == "list-assemblies":
        cli_list_assemblies(args)

    elif args.command == "render":
        cli_render(args)

    elif args.command == "show":
        cli_show(args)

    else:
        print("Unknown command.\n")
        parser.print_help()


if __name__ == "__main__":
    main()
